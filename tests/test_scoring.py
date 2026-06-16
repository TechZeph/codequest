from codequest.scoring import apply_quest_xp, calculate_level, calculate_rank


def test_level_calculation_uses_100_xp_steps():
    assert calculate_level(0) == 0
    assert calculate_level(99) == 0
    assert calculate_level(100) == 1
    assert calculate_level(250) == 2


def test_rank_calculation_caps_at_system_builder():
    assert calculate_rank(0) == "Copy-Paster"
    assert calculate_rank(5) == "Repo Smith"
    assert calculate_rank(99) == "System Builder"


def test_apply_quest_xp_updates_total_level_and_stats():
    profile = {
        "total_xp": 90,
        "level": 0,
        "rank": "Copy-Paster",
        "stat_xp": {"cli": 5},
        "achievements": [],
    }
    quest = {"skills": {"cli": 10, "testing": 20}}

    updated = apply_quest_xp(profile, quest)

    assert updated["total_xp"] == 120
    assert updated["level"] == 1
    assert updated["rank"] == "Script Goblin"
    assert updated["stat_xp"]["cli"] == 15
    assert updated["stat_xp"]["testing"] == 20

