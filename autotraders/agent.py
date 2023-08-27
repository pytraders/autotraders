from typing import Optional
import re

from autotraders.error import SpaceTradersException
from autotraders.faction.contract import Contract
from autotraders.paginated_list import PaginatedList
from autotraders.shared_models.map_symbol import MapSymbol
from autotraders.space_traders_entity import SpaceTradersEntity
from autotraders.session import AutoTradersSession
from autotraders.ship import Ship


class Agent(SpaceTradersEntity):
    contracts: Optional[PaginatedList]
    starting_faction: str
    symbol: str
    account_id: str
    credits: int
    ship_count: int
    ships: Optional[PaginatedList]
    headquarters: MapSymbol

    def __init__(self, session: AutoTradersSession, symbol=None, data=None):
        """
        :param symbol: If it's None, then the agent associated with the token will be retrieved.
            Otherwise, the specified agent will be retrieved.
        """
        if symbol is None:
            super().__init__(session, "my/agent", data)
        else:
            super().__init__(session, "agents/" + symbol, data)

    def update(self, data=None):
        data = super()._update(data)
        mappings = {
            "account_id": {"type": None, "class": str, "alias": "accountId"},
            "symbol": {"type": None, "class": str},
            "headquarters": {"type": None, "class": MapSymbol},
            "credits": {"type": None, "class": int},
            "starting_faction": {"type": None, "class": str, "alias": "startingFaction"},
            "ship_count": {"type": None, "class": int, "alias": "shipCount"},
        }
        super().update_attr(mappings, data)

    @staticmethod
    def create(session, faction, symbol, email, override_email_check=False):
        def check_email(e):
            return re.fullmatch(r"^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$", e)

        if not override_email_check and not (email is None or check_email(email)):
            raise ValueError(
                email
                + " is not a valid email. Use override_email_check=True to bypass this error."
            )
        r = session.post(
            session.b_url + "register",
            json={
                "faction": faction.upper(),
                "symbol": symbol,
                "email": email,
            },
        )
        j = r.json()
        if "error" in j:
            raise SpaceTradersException(j["error"], r.status_code)
        return j["data"]["token"]

    @staticmethod
    def all(session, page: int = 1) -> PaginatedList:
        def paginated_func(p, num_per_page):
            r = session.get(
                session.b_url + "agents?limit=" + str(num_per_page) + "&page=" + str(p)
            )
            j = r.json()
            if "error" in j:
                raise SpaceTradersException(j["error"], r.status_code)
            agents = []
            for agent in j["data"]:
                a = Agent(session, agent["symbol"], agent)
                agents.append(a)
            return agents, r.json()["meta"]["total"]

        return PaginatedList(paginated_func, page)
