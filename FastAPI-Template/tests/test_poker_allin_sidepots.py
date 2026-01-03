from src.poker import poker_manager
from src.poker.deck_manager import build_standard_52_deck
from src.poker.manager import TableConfig


def _force_fixed_hand_cards(*, table, hand_id: str, hole_cards_by_user: dict[int, list[str]], board5: list[str]) -> None:
    hand = table.state.hand
    assert hand is not None
    assert hand.hand_id == hand_id
    assert len(board5) == 5

    used = set(board5)
    for uid, cards in hole_cards_by_user.items():
        assert len(cards) == 2
        used.update(cards)

    # Choose burn cards not colliding with used cards.
    burns: list[str] = []
    for c in build_standard_52_deck():
        if c in used:
            continue
        burns.append(c)
        if len(burns) == 3:
            break
    assert len(burns) == 3

    flop1, flop2, flop3, turn, river = board5
    burn1, burn2, burn3 = burns

    # _runout_to_showdown_locked pops from the end:
    # burn1, flop1, flop2, flop3, burn2, turn, burn3, river
    tail = [
        river,
        burn3,
        turn,
        burn2,
        flop3,
        flop2,
        flop1,
        burn1,
    ]

    deck = [c for c in build_standard_52_deck() if c not in used and c not in set(tail)]
    hand.deck = deck + tail
    hand.board = []
    hand.burned = []
    hand.hole_cards = {int(uid): list(cards) for uid, cards in hole_cards_by_user.items()}


def _first_event_for_hand(events: list[dict], *, hand_id: str, event_type: str) -> dict:
    for e in events:
        if e.get("type") != event_type:
            continue
        payload = e.get("payload") or {}
        if payload.get("hand_id") == hand_id:
            return e
    raise AssertionError(f"missing event {event_type} for hand {hand_id}")


class TestPokerAllInSidePots:
    async def test_all_in_3p_main_and_side_pot_different_winners(self):
        # sb/bb=0 so auto-continue won't change stacks in the next hand.
        table = await poker_manager.create_table(
            name="T_allin_3p_sidepot",
            max_players=6,
            config=TableConfig(sb=0, bb=0, min_buyin=1, max_buyin=1000, action_timeout_sec=5),
        )

        # Seat 1: 10, Seat 2: 5, Seat 3: 10
        for uid, amt, seat_no in [(1, 10, 1), (2, 5, 2), (3, 10, 3)]:
            await table.ensure_member(user_id=uid, username=f"u{uid}")
            await table.buyin(user_id=uid, amount=amt)
            await table.sit(user_id=uid, seat_no=seat_no)

        # Sitting the 2nd player auto-starts a hand; restart to include all 3.
        async with table._locked_state():
            table.state.hand = None
            table.state.last_button_seat = None
        await table._maybe_start_hand()
        assert table.state.hand is not None
        hand_id = table.state.hand.hand_id

        # Make seat2 win main pot (straight), seat1 win side pot (pair aces) over seat3.
        _force_fixed_hand_cards(
            table=table,
            hand_id=hand_id,
            hole_cards_by_user={
                1: ["AS", "AD"],
                2: ["5H", "6H"],
                3: ["KH", "QC"],
            },
            board5=["2H", "3D", "4S", "9C", "KD"],
        )

        # Preflop action: seat1 raises all-in to 10, seat2 calls all-in (5), seat3 calls all-in (10).
        await table.handle_action(user_id=1, action="raise_to", amount=10)
        await table.handle_action(user_id=2, action="call")
        await table.handle_action(user_id=3, action="call")

        events = await table.fetch_events_since(0)

        # Verify runout + showdown for this hand_id.
        street_events = [
            e
            for e in events
            if e.get("type") == "STREET_DEALT" and (e.get("payload") or {}).get("hand_id") == hand_id
        ]
        assert [e["payload"]["street"] for e in street_events] == ["FLOP", "TURN", "RIVER"]

        showdown = _first_event_for_hand(events, hand_id=hand_id, event_type="SHOWDOWN")
        assert showdown["payload"]["board"] == ["2H", "3D", "4S", "9C", "KD"]
        assert showdown["payload"]["side_pots"] == [
            {"amount": 15, "eligible_seats": [1, 2, 3]},
            {"amount": 10, "eligible_seats": [1, 3]},
        ]
        assert showdown["payload"]["payouts"] == {"2": 15, "1": 10}

    async def test_all_in_3p_split_pot_with_odd_chip_remainder(self):
        table = await poker_manager.create_table(
            name="T_allin_3p_split",
            max_players=6,
            config=TableConfig(sb=0, bb=0, min_buyin=1, max_buyin=1000, action_timeout_sec=5),
        )

        # Three players with equal stacks: each all-in 5 => pot=15 (odd).
        for uid, amt, seat_no in [(1, 5, 1), (2, 5, 2), (3, 5, 3)]:
            await table.ensure_member(user_id=uid, username=f"u{uid}")
            await table.buyin(user_id=uid, amount=amt)
            await table.sit(user_id=uid, seat_no=seat_no)

        # Restart to include all 3 players in the same hand.
        async with table._locked_state():
            table.state.hand = None
            table.state.last_button_seat = None
        await table._maybe_start_hand()
        assert table.state.hand is not None
        hand_id = table.state.hand.hand_id

        # Seat1 and Seat2 both make Broadway straight (need a Ten); seat3 loses.
        _force_fixed_hand_cards(
            table=table,
            hand_id=hand_id,
            hole_cards_by_user={
                1: ["TS", "3C"],
                2: ["TH", "4C"],
                3: ["9S", "9D"],
            },
            board5=["AS", "KD", "QH", "JC", "2D"],
        )

        await table.handle_action(user_id=1, action="raise_to", amount=5)
        await table.handle_action(user_id=2, action="call")
        await table.handle_action(user_id=3, action="call")

        events = await table.fetch_events_since(0)
        showdown = _first_event_for_hand(events, hand_id=hand_id, event_type="SHOWDOWN")

        # 15 split two ways => 7 each, remainder 1 goes to lowest seat among winners (seat1).
        assert showdown["payload"]["side_pots"] == [{"amount": 15, "eligible_seats": [1, 2, 3]}]
        assert showdown["payload"]["payouts"] == {"1": 8, "2": 7}

    async def test_all_in_4p_two_side_pots(self):
        table = await poker_manager.create_table(
            name="T_allin_4p_twosidepots",
            max_players=9,
            config=TableConfig(sb=0, bb=0, min_buyin=1, max_buyin=1000, action_timeout_sec=5),
        )

        # Contributions target (all-in): seat1=10, seat2=5, seat3=3, seat4=10.
        for uid, amt, seat_no in [(1, 10, 1), (2, 5, 2), (3, 3, 3), (4, 10, 4)]:
            await table.ensure_member(user_id=uid, username=f"u{uid}")
            await table.buyin(user_id=uid, amount=amt)
            await table.sit(user_id=uid, seat_no=seat_no)

        # Restart to include all 4 players in the same hand.
        async with table._locked_state():
            table.state.hand = None
            table.state.last_button_seat = None
        await table._maybe_start_hand()
        assert table.state.hand is not None
        hand_id = table.state.hand.hand_id

        # Ranking: seat3 straight > seat2 AA > seat4 KK > seat1 QQ
        _force_fixed_hand_cards(
            table=table,
            hand_id=hand_id,
            hole_cards_by_user={
                1: ["QH", "QS"],
                2: ["AS", "AD"],
                3: ["5H", "6H"],
                4: ["KH", "QC"],
            },
            board5=["2H", "3D", "4S", "9C", "KD"],
        )

        # Acting starts after bb_seat (seat3) => seat4.
        await table.handle_action(user_id=4, action="raise_to", amount=10)
        await table.handle_action(user_id=1, action="call")
        await table.handle_action(user_id=2, action="call")
        await table.handle_action(user_id=3, action="call")

        events = await table.fetch_events_since(0)
        showdown = _first_event_for_hand(events, hand_id=hand_id, event_type="SHOWDOWN")

        assert showdown["payload"]["side_pots"] == [
            {"amount": 12, "eligible_seats": [1, 2, 3, 4]},
            {"amount": 6, "eligible_seats": [1, 2, 4]},
            {"amount": 10, "eligible_seats": [1, 4]},
        ]
        assert showdown["payload"]["payouts"] == {"3": 12, "2": 6, "4": 10}
