from caqf_exp.config import load_yaml, validate_campaign


def test_campaign_contract():
    c = load_yaml("config/campaign.yaml")
    assert validate_campaign(c) == []
    assert c["repetitions"] == 5
    assert len(c["controlled_conditions"]) == 5
