from src.poker import poker_manager
from src.poker.manager import TableConfig
from core.exceptions import BusinessError


class TestPokerPreflopEngine:
    async def test_preflop_call_check_completes_round(self):
        table = await poker_manager.create_table(
            name="T_preflop",
            max_players=6,
            config=TableConfig(
                sb=1, bb=2, min_buyin=1, max_buyin=1000, action_timeout_sec=5
            ),
        )

        await table.ensure_member(user_id=1, username="u1")
        await table.ensure_member(user_id=2, username="u2")
        await table.buyin(user_id=1, amount=100)
        await table.buyin(user_id=2, amount=100)
        await table.sit(user_id=1, seat_no=1)
        await table.sit(user_id=2, seat_no=2)

        assert table.state.hand is not None
        hand_id = table.state.hand.hand_id

        # Heads-up: button posts SB and acts first preflop.
        assert table.state.hand.button_seat == 1
        assert table.state.hand.sb_seat == 1
        assert table.state.hand.bb_seat == 2
        assert table.state.hand.acting_seat == 1

        await table.handle_action(user_id=1, action="call")
        assert table.state.hand is not None
        assert table.state.hand.hand_id == hand_id
        assert table.state.hand.acting_seat == 2

        await table.handle_action(user_id=2, action="check")
        assert table.state.hand is not None
        assert table.state.hand.street == "FLOP"
        # Postflop: BB acts first.
        assert table.state.hand.acting_seat == 2

        events = await table.fetch_events_since(0)
        types = [e.get("type") for e in events]
        assert "HAND_STARTED" in types
        assert "ACTION_TAKEN" in types
        assert "PREFLOP_COMPLETED" in types
        assert "STREET_DEALT" in types

    async def test_timeout_auto_fold_ends_hand(self):
        table = await poker_manager.create_table(
            name="T_timeout",
            max_players=6,
            config=TableConfig(
                sb=1, bb=2, min_buyin=1, max_buyin=1000, action_timeout_sec=1
            ),
        )

        await table.ensure_member(user_id=10, username="u10")
        await table.ensure_member(user_id=20, username="u20")
        await table.buyin(user_id=10, amount=100)
        await table.buyin(user_id=20, amount=100)
        await table.sit(user_id=10, seat_no=1)
        await table.sit(user_id=20, seat_no=2)

        assert table.state.hand is not None
        first_hand_id = table.state.hand.hand_id
        deadline = table.state.hand.action_deadline_ms

        # Trigger timeout processing without real sleeping.
        await poker_manager.timeout_tick_for_tests(deadline + 1)

        # Auto-continue is enabled: after the fold ends the hand, a new hand starts
        # immediately (if there are still >=2 active seated players).
        assert table.state.hand is not None
        assert table.state.hand.hand_id != first_hand_id

        # Hand1: seat 1 posted SB(1) and timed out (fold); seat 2 wins pot (3)
        # => stacks become (99, 101). Hand2 starts right away and posts blinds again
        # with rotated button (seat 2 SB=1, seat 1 BB=2) => stacks become (97, 100).
        assert table.state.seats[1].stack == 97
        assert table.state.seats[2].stack == 100

    async def test_spectate_during_hand_force_folds_and_ends_heads_up(self):
        table = await poker_manager.create_table(
            name="T_spectate_force_fold",
            max_players=6,
            config=TableConfig(
                sb=1, bb=2, min_buyin=1, max_buyin=1000, action_timeout_sec=5
            ),
        )

        await table.ensure_member(user_id=1, username="u1")
        await table.ensure_member(user_id=2, username="u2")
        await table.buyin(user_id=1, amount=100)
        await table.buyin(user_id=2, amount=100)
        await table.sit(user_id=1, seat_no=1)
        await table.sit(user_id=2, seat_no=2)

        assert table.state.hand is not None

        # Heads-up: acting seat is the button/SB.
        assert table.state.hand.acting_seat == 1

        # Spectate should force-fold seat 2 and end the hand.
        await table.spectate(user_id=2)
        assert table.state.hand is None
        assert 2 not in table.state.seats

        # Seat 1 wins the pot (3) after posting SB(1).
        assert table.state.seats[1].stack == 102

    async def test_action_token_mismatch_rejected(self):
        table = await poker_manager.create_table(
            name="T_action_token",
            max_players=6,
            config=TableConfig(
                sb=1, bb=2, min_buyin=1, max_buyin=1000, action_timeout_sec=5
            ),
        )

        await table.ensure_member(user_id=1, username="u1")
        await table.ensure_member(user_id=2, username="u2")
        await table.buyin(user_id=1, amount=100)
        await table.buyin(user_id=2, amount=100)
        await table.sit(user_id=1, seat_no=1)
        await table.sit(user_id=2, seat_no=2)

        assert table.state.hand is not None
        assert table.state.hand.acting_seat == 1

        bad_token = int(table.state.hand.action_token) + 999
        try:
            await table.handle_action(
                user_id=1,
                action="call",
                action_token=bad_token,
            )
            raise AssertionError("expected BusinessError")
        except BusinessError as e:
            assert e.i18n_key == "poker.invalid_action_token"

        ok_token = int(table.state.hand.action_token)
        await table.handle_action(
            user_id=1,
            action="call",
            action_token=ok_token,
        )
