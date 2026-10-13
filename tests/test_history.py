from bot.history import ChatHistory, ChatLine


def test_keeps_last_n_per_chat():
    h = ChatHistory(size=2)
    for i in range(3):
        h.add(1, "A", f"m{i}")
    h.add(2, "B", "other")
    assert h.recent(1) == [ChatLine("A", "m1"), ChatLine("A", "m2")]
    assert h.recent(2) == [ChatLine("B", "other")]
    assert h.recent(3) == []


def test_ignores_blank_and_zero_size():
    h = ChatHistory(size=5)
    h.add(1, "A", "   ")
    assert h.recent(1) == []
    h0 = ChatHistory(size=0)
    h0.add(1, "A", "hi")
    assert h0.recent(1) == []
