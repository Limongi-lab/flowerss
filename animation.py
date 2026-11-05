import numpy as np
import config
from bezier import phase_progress, ease_in_out


class AnimationController:
    def __init__(self, cloud):
        self._cloud = cloud
        self._appear_times = cloud.appear_times

    def visible_count(self, elapsed):
        return int(np.searchsorted(self._appear_times, elapsed, side="right"))

    def message_alpha(self, elapsed):
        return ease_in_out(phase_progress(elapsed, config.T_MSG_FADE_START, config.T_MSG_FADE_END))

    def name_alpha(self, elapsed):
        return ease_in_out(phase_progress(elapsed, config.T_NAME_FADE_START, config.T_NAME_FADE_END))

    def is_complete(self, elapsed):
        return elapsed >= config.T_TOTAL
