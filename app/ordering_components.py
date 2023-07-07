"""Compute scores for each result in the given message."""


def get_confidence(result, message, logger):
    """
    This function iterates through the results from multiple ARAs,
    If only a single score is non-zero the result is thresholded to be in [0,1-eps] 
    If a result has non-zero scores from multiple ARAs,
    then all the scores are added together and thresholded to be in [0,1]
    
    eps is set to 0.001
    """
    score_sum = 0
    non_zero_count = 0
    eps = 0.001
    for analysis in result.get("analyses") or []:
        if analysis.get("score") is not None:
            score_sum += analysis["score"]
            if analysis["score"] > 0:
                non_zero_count += 1
    if non_zero_count == 1 and score_sum > 1 - eps:
        score_sum = 1 - eps
    elif non_zero_count > 1 and score_sum > 1:
        score_sum = 1
    return score_sum


def get_clinical_evidence(result, message, logger):
    # TODO Calculate clinical evidence
    return 0


def get_novelty(result, message, logger):
    # TODO get novelty from novelty package
    return 0


def get_ordering_components(message, logger):
    logger.debug(f"Computing scores for {len(message['results'])} results")
    for result in message.get("results") or []:
        result["ordering_components"] = {
            "confidence": get_confidence(result, message, logger),
            "clinical_evidence": get_clinical_evidence(result, message, logger),
            "novelty": get_novelty(result, message, logger),
        }
