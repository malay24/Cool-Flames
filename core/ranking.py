"""Transparent weighted ranking score (CLAUDE.md section 8.2).

Task R2. score = w1*area_match + w2*condition_overlap
             + w3*fuel_realism + w4*data_richness
Default weights w1=0.35, w2=0.30, w3=0.20, w4=0.15. No LLM in the explanation.
"""

# TODO (R2): four [0,1] components, weights as args, template explanation.
