class UserProfileEngine:
    def merge_feedback_summary(self, *, profile: dict, feedback_summary: dict):
        preferred_product_keys = self._merge_unique(
            profile.get("preferred_product_keys", []),
            feedback_summary.get("preferred_product_keys", []),
        )
        avoided_product_keys = self._merge_unique(
            profile.get("avoided_product_keys", []),
            feedback_summary.get("avoided_product_keys", []),
        )

        profile_score = self._score_profile(
            preferred_product_keys=preferred_product_keys,
            avoided_product_keys=avoided_product_keys,
            preferred_marketplaces=profile.get("preferred_marketplaces", []),
            preferred_brands=profile.get("preferred_brands", []),
        )

        return {
            **profile,
            "preferred_product_keys": preferred_product_keys,
            "avoided_product_keys": avoided_product_keys,
            "profile_score": profile_score,
            "metadata": {
                **profile.get("metadata", {}),
                "profile_version": "user_profile_v1",
                "last_feedback_event_count": feedback_summary.get("event_count", 0),
            },
        }

    def apply_manual_preferences(self, *, profile: dict, preferences: dict):
        merged = {
            **profile,
            "preferred_marketplaces": self._merge_unique(
                profile.get("preferred_marketplaces", []),
                preferences.get("preferred_marketplaces", []),
            ),
            "blocked_marketplaces": self._merge_unique(
                profile.get("blocked_marketplaces", []),
                preferences.get("blocked_marketplaces", []),
            ),
            "preferred_brands": self._merge_unique(
                profile.get("preferred_brands", []),
                preferences.get("preferred_brands", []),
            ),
            "risk_tolerance": preferences.get("risk_tolerance") or profile.get("risk_tolerance", "MEDIUM"),
        }
        merged["profile_score"] = self._score_profile(
            preferred_product_keys=merged.get("preferred_product_keys", []),
            avoided_product_keys=merged.get("avoided_product_keys", []),
            preferred_marketplaces=merged.get("preferred_marketplaces", []),
            preferred_brands=merged.get("preferred_brands", []),
        )
        merged["metadata"] = {
            **profile.get("metadata", {}),
            "profile_version": "user_profile_v1",
            "manual_preferences_applied": True,
        }
        return merged

    def recommendation_context(self, *, profile: dict):
        return {
            "user_id": profile["user_id"],
            "preferred_marketplaces": profile.get("preferred_marketplaces", []),
            "blocked_marketplaces": profile.get("blocked_marketplaces", []),
            "preferred_brands": profile.get("preferred_brands", []),
            "preferred_product_keys": profile.get("preferred_product_keys", []),
            "avoided_product_keys": profile.get("avoided_product_keys", []),
            "risk_tolerance": profile.get("risk_tolerance", "MEDIUM"),
            "profile_score": profile.get("profile_score", 0),
            "metadata": {"context_version": "user_profile_context_v1"},
        }

    def _merge_unique(self, left: list[str], right: list[str]):
        return list(dict.fromkeys([*(left or []), *(right or [])]))

    def _score_profile(
        self,
        *,
        preferred_product_keys: list[str],
        avoided_product_keys: list[str],
        preferred_marketplaces: list[str],
        preferred_brands: list[str],
    ):
        score = 0
        score += min(30, len(preferred_product_keys) * 10)
        score += min(20, len(avoided_product_keys) * 5)
        score += min(25, len(preferred_marketplaces) * 10)
        score += min(25, len(preferred_brands) * 10)
        return max(0, min(100, score))
