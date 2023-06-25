async def get_approval_status(result, message):
    for nbindings in result["node_bindings"].items():
        for node in nbindings:
            for attribute in message["knowledge_graph"]["nodes"][node["id"]]["attributes"]:
                if attribute["attribute_type_id"] is "biothings_annotations":
                    # This returns 1 of 5 values: 0, .25, .5, .75, 1, depending on the max phase.
                    # TODO Determine proper appraisal of approval status
                    max_phase = attribute["value"].get("chembl", 0).get("max_phase", 0)
                    return max_phase/4
            
async def get_confidence(result, message):
    # TODO Implement actual g()-score
    score_sum = 0
    score_count = 0
    for analysis in result:
        if analysis.get("score") is not None:
            score_sum += analysis["score"]
            score_count += 1
    return score_sum / score_count


async def get_clinical_evidence(result, message):
    # TODO Calculate clinical evidence
    return 0

async def get_novelty(result, message):
    # TODO get novelty from novelty package
    return 0
                
async def get_ordering_components(message):
    for result in message["results"]:
        result["ordering_components"] = {
            "drug_approval": get_approval_status(result, message),
            "confidence": get_confidence(result, message),
            "clinical_evidence": get_clinical_evidence(result, message),
            "novelty": get_novelty(result, message)
        }