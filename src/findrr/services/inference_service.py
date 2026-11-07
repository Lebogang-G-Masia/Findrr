"""Unified machine learning inference service (Module 9 & Module 3)."""

import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from findrr.ml.application_tailor_runner import (
    MockApplicationTailorRunner,
    ONNXApplicationTailorRunner,
)
from findrr.ml.base import IModelRunner
from findrr.ml.registry import ModelRegistry
from findrr.ml.similarity_evaluator_runner import (
    MockSimilarityEvaluatorRunner,
    SimilarityEvaluatorRunner,
)
from findrr.ml.title_expander_runner import (
    MockTitleExpanderRunner,
    TitleExpanderRunner,
)

logger = logging.getLogger(__name__)


class TitleExpansionResult(BaseModel):
    """Result payload for generative title expansion."""

    generalized_title: str
    expanded_titles: List[str]
    model_id: str
    model_version: str
    is_mock: bool


class SimilarityResult(BaseModel):
    """Result payload for text semantic similarity."""

    text_a: str
    text_b: str
    similarity_score: float
    model_id: str
    model_version: str
    is_mock: bool


class ValidatedCandidate(BaseModel):
    """Candidate title evaluated through relevance and deduplication filters."""

    term: str
    similarity_score: float
    status: str = Field(description="ACCEPTED, REJECTED_LOW_SCORE, REJECTED_DUPLICATE")
    model_version: str
    is_mock: bool


class InferenceService:
    """Central inference service engine coordinating Model 1 and Model 2 execution."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        force_mock: Optional[bool] = None,
    ):
        self.registry = registry or ModelRegistry()
        env_mock = os.getenv("FINDRR_MOCK_INFERENCE", "false").lower() in ("true", "1")
        self.force_mock = force_mock if force_mock is not None else env_mock
        self._runners: Dict[str, IModelRunner] = {}

    def _get_title_expander(self) -> IModelRunner:
        model_id = "ML-001"
        if model_id in self._runners:
            return self._runners[model_id]

        if self.force_mock:
            runner = MockTitleExpanderRunner()
        else:
            status = self.registry.inspect_model_status(model_id)
            if status["integrity_verified"]:
                artifact_dir = self.registry.get_artifact_dir(model_id)
                runner = TitleExpanderRunner(artifact_dir, version=status["version"])
            else:
                logger.warning(
                    "Real Model 1 artifacts not available or unverified (%s). "
                    "Falling back to explicit MOCK runner.",
                    status.get("error"),
                )
                runner = MockTitleExpanderRunner()

        self._runners[model_id] = runner
        return runner

    def _get_similarity_evaluator(self) -> IModelRunner:
        model_id = "ML-002"
        if model_id in self._runners:
            return self._runners[model_id]

        if self.force_mock:
            runner = MockSimilarityEvaluatorRunner()
        else:
            status = self.registry.inspect_model_status(model_id)
            if status["integrity_verified"]:
                artifact_dir = self.registry.get_artifact_dir(model_id)
                runner = SimilarityEvaluatorRunner(artifact_dir, version=status["version"])
            else:
                logger.warning(
                    "Real Model 2 artifacts not available or unverified (%s). "
                    "Falling back to explicit MOCK runner.",
                    status.get("error"),
                )
                runner = MockSimilarityEvaluatorRunner()

        self._runners[model_id] = runner
        return runner

    def _get_application_tailor(self) -> IModelRunner:
        model_id = "ML-003"
        if model_id in self._runners:
            return self._runners[model_id]

        if self.force_mock:
            runner = MockApplicationTailorRunner()
        else:
            status = self.registry.inspect_model_status(model_id)
            if status["integrity_verified"]:
                artifact_dir = self.registry.get_artifact_dir(model_id)
                runner = ONNXApplicationTailorRunner(artifact_dir)
            else:
                logger.warning(
                    "Real Model 3 artifacts not available or unverified (%s). "
                    "Falling back to explicit MOCK runner.",
                    status.get("error"),
                )
                runner = MockApplicationTailorRunner()

        self._runners[model_id] = runner
        return runner

    def expand_titles(
        self,
        generalized_title: str,
        skills: List[str],
        seniority: Optional[str] = None,
    ) -> TitleExpansionResult:
        """Expand generalized title into candidate search titles via Model 1."""
        runner = self._get_title_expander()
        candidates = runner.expand(generalized_title, skills, seniority)
        return TitleExpansionResult(
            generalized_title=generalized_title,
            expanded_titles=candidates,
            model_id="ML-001",
            model_version=runner.version,
            is_mock=runner.is_mock,
        )

    def evaluate_similarity(self, text_a: str, text_b: str) -> SimilarityResult:
        """Compute dense semantic similarity score via Model 2."""
        runner = self._get_similarity_evaluator()
        score = runner.evaluate_pair(text_a, text_b)
        return SimilarityResult(
            text_a=text_a,
            text_b=text_b,
            similarity_score=score,
            model_id="ML-002",
            model_version=runner.version,
            is_mock=runner.is_mock,
        )

    def filter_and_validate_candidates(
        self,
        primary_title: str,
        candidates: List[str],
        relevance_threshold: float = 0.70,
        dedup_threshold: float = 0.88,
    ) -> List[ValidatedCandidate]:
        """Apply relevance thresholding and near-duplicate filtering (FR-009, FR-010, FR-011)."""
        runner = self._get_similarity_evaluator()
        evaluated: List[ValidatedCandidate] = []
        accepted_terms: List[str] = []

        # 1. Relevance scoring against primary generalized title
        for cand in candidates:
            sim = runner.evaluate_pair(primary_title, cand)
            if sim < relevance_threshold:
                evaluated.append(
                    ValidatedCandidate(
                        term=cand,
                        similarity_score=sim,
                        status="REJECTED_LOW_SCORE",
                        model_version=runner.version,
                        is_mock=runner.is_mock,
                    )
                )
                continue

            # 2. Near-duplicate filtering against already accepted terms
            is_duplicate = False
            for accepted in accepted_terms:
                inter_sim = runner.evaluate_pair(accepted, cand)
                if inter_sim >= dedup_threshold:
                    evaluated.append(
                        ValidatedCandidate(
                            term=cand,
                            similarity_score=sim,
                            status="REJECTED_DUPLICATE",
                            model_version=runner.version,
                            is_mock=runner.is_mock,
                        )
                    )
                    is_duplicate = True
                    break

            if not is_duplicate:
                accepted_terms.append(cand)
                evaluated.append(
                    ValidatedCandidate(
                        term=cand,
                        similarity_score=sim,
                        status="ACCEPTED",
                        model_version=runner.version,
                        is_mock=runner.is_mock,
                    )
                )

        return evaluated

    def tailor_statement(
        self,
        target_role: str,
        company: str,
        job_requirements: List[str],
        verified_user_facts: List[str],
    ) -> Dict[str, Any]:
        """Generate tailored fact-grounded statement using Model 3 (ML-003, US-013)."""
        runner = self._get_application_tailor()
        return runner.generate_statement(
            target_role=target_role,
            company=company,
            job_requirements=job_requirements,
            verified_user_facts=verified_user_facts,
        )

    def unload_model(self, model_id: str) -> None:
        """Explicitly unload a model from memory to respect host memory limits."""
        if model_id in self._runners:
            self._runners[model_id].unload()
            del self._runners[model_id]
            logger.info("Unloaded model %s from inference service", model_id)

    def unload_all(self) -> None:
        """Unload all active model runners from memory."""
        for mid in list(self._runners.keys()):
            self.unload_model(mid)
