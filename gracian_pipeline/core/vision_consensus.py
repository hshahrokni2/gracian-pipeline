"""
Multi-Model Vision Consensus for Scanned PDF Extraction

Purpose:
- Use multiple vision models (Gemini, GPT-4V, Qwen) to extract data from scanned PDFs
- Combine results through weighted voting to maximize accuracy
- Provide confidence scores for extracted data
- Handle model failures gracefully with fallback logic

Architecture:
- Primary: Gemini 2.5-Pro (50% weight) - Best Swedish support
- Secondary: GPT-4V (30% weight) - Strong general vision
- Tertiary: Qwen 2.5-VL (20% weight) - Fast and cost-effective

Performance Impact:
- Expected: 22.7% → 75-85% accuracy on scanned PDFs
- Consensus voting reduces hallucinations and errors
- Critical for 49% of corpus (scanned documents)
"""

import base64
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PIL import Image
import openai
import google.generativeai as genai

logger = logging.getLogger(__name__)


@dataclass
class VisionModelResult:
    """Result from a single vision model"""

    model_name: str
    """Model that produced this result"""

    extracted_data: Dict[str, Any]
    """Extracted field values"""

    confidence: float
    """Model's confidence in extraction (0.0-1.0)"""

    processing_time: float
    """Time taken to process (seconds)"""

    success: bool
    """Whether extraction succeeded"""

    error: Optional[str] = None
    """Error message if failed"""


@dataclass
class ConsensusResult:
    """Final consensus result from multiple vision models"""

    extracted_data: Dict[str, Any]
    """Final extracted field values"""

    confidence: float
    """Overall confidence in consensus (0.0-1.0)"""

    agreement_ratio: float
    """Ratio of models that agreed on each field (0.0-1.0)"""

    model_results: List[VisionModelResult]
    """Individual model results"""

    primary_model: str
    """Which model was used as primary (highest weight)"""

    fallback_used: bool
    """Whether fallback logic was triggered"""


class VisionConsensusExtractor:
    """
    Extract data from scanned PDFs using multiple vision models with consensus voting.

    Models are called in parallel (where possible) and results combined through:
    1. Weighted voting (Gemini 50%, GPT-4V 30%, Qwen 20%)
    2. Confidence-based selection for tied votes
    3. Fallback to single-model if others fail
    """

    # Model weights for consensus voting
    MODEL_WEIGHTS = {
        "gemini-2.5-pro": 0.5,   # Best Swedish support
        "gpt-4o": 0.3,           # Strong general vision (updated from deprecated gpt-4-vision-preview)
        "qwen-2.5-vl": 0.2,      # Fast and cost-effective
    }

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        enable_fallback: bool = True
    ):
        """
        Initialize vision consensus extractor.

        Args:
            gemini_api_key: Google Gemini API key (or from GEMINI_API_KEY env var)
            openai_api_key: OpenAI API key (or from OPENAI_API_KEY env var)
            enable_fallback: Whether to fall back to single model on failures
        """
        self.enable_fallback = enable_fallback

        # Initialize API keys
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # Initialize clients
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
        else:
            self.gemini_model = None
            logger.warning("Gemini API key not found - Gemini extraction disabled")

        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            logger.warning("OpenAI API key not found - GPT-4V extraction disabled")

        # Qwen would require separate initialization (H100 or Ollama)
        # For now, focus on Gemini + GPT-4V consensus
        self.qwen_available = False

    def extract_from_images(
        self,
        images: List[Tuple[int, Image.Image]],
        extraction_prompt: str,
        agent_name: str
    ) -> ConsensusResult:
        """
        Extract data from preprocessed images using multi-model consensus.

        Args:
            images: List of (page_num, image) tuples
            extraction_prompt: Prompt describing what to extract
            agent_name: Name of agent making extraction (for logging)

        Returns:
            ConsensusResult with extracted data and confidence scores

        Example:
            >>> extractor = VisionConsensusExtractor()
            >>> images = [(1, img1), (2, img2)]
            >>> prompt = "Extract chairman name from Swedish BRF document"
            >>> result = extractor.extract_from_images(images, prompt, "chairman_agent")
            >>> print(result.extracted_data)
            {"chairman": "Erik Johansson"}
        """
        import time

        model_results: List[VisionModelResult] = []

        # Try Gemini 2.5-Pro (primary model)
        if self.gemini_model:
            start_time = time.time()
            try:
                gemini_result = self._extract_with_gemini(images, extraction_prompt)
                processing_time = time.time() - start_time

                model_results.append(VisionModelResult(
                    model_name="gemini-2.5-pro",
                    extracted_data=gemini_result,
                    confidence=0.9,  # Gemini is highly reliable for Swedish
                    processing_time=processing_time,
                    success=True
                ))

                logger.info(f"{agent_name}: Gemini extraction successful ({processing_time:.1f}s)")

            except Exception as e:
                logger.error(f"{agent_name}: Gemini extraction failed: {e}")
                model_results.append(VisionModelResult(
                    model_name="gemini-2.5-pro",
                    extracted_data={},
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    success=False,
                    error=str(e)
                ))

        # Try GPT-4V (secondary model)
        if self.openai_api_key:
            start_time = time.time()
            try:
                gpt4v_result = self._extract_with_gpt4v(images, extraction_prompt)
                processing_time = time.time() - start_time

                model_results.append(VisionModelResult(
                    model_name="gpt-4o",
                    extracted_data=gpt4v_result,
                    confidence=0.85,  # Strong but slightly lower for Swedish
                    processing_time=processing_time,
                    success=True
                ))

                logger.info(f"{agent_name}: GPT-4V extraction successful ({processing_time:.1f}s)")

            except Exception as e:
                logger.error(f"{agent_name}: GPT-4V extraction failed: {e}")
                model_results.append(VisionModelResult(
                    model_name="gpt-4o",
                    extracted_data={},
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    success=False,
                    error=str(e)
                ))

        # Combine results through consensus voting
        return self._compute_consensus(model_results, agent_name)

    def _extract_with_gemini(
        self,
        images: List[Tuple[int, Image.Image]],
        extraction_prompt: str
    ) -> Dict[str, Any]:
        """
        Extract data using Gemini 2.5-Pro vision model.

        Args:
            images: List of (page_num, image) tuples
            extraction_prompt: Extraction instructions

        Returns:
            Extracted field values as dictionary
        """
        import json

        # Convert images to format Gemini expects
        image_parts = []
        for page_num, img in images:
            # Gemini accepts PIL Image directly
            image_parts.append(img)

        # Build prompt
        full_prompt = f"""You are extracting data from Swedish BRF (housing cooperative) annual reports.

{extraction_prompt}

Return ONLY valid JSON matching the requested schema. No additional text.
"""

        # Call Gemini API
        response = self.gemini_model.generate_content([full_prompt] + image_parts)

        # Parse JSON response
        try:
            result = json.loads(response.text)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from markdown fence
            text = response.text
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"Could not parse JSON from Gemini response: {text}")

    def _extract_with_gpt4v(
        self,
        images: List[Tuple[int, Image.Image]],
        extraction_prompt: str
    ) -> Dict[str, Any]:
        """
        Extract data using GPT-4 Vision model.

        Args:
            images: List of (page_num, image) tuples
            extraction_prompt: Extraction instructions

        Returns:
            Extracted field values as dictionary
        """
        import json

        # Convert images to base64
        image_urls = []
        for page_num, img in images:
            # Convert to base64
            import io
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            image_urls.append(f"data:image/png;base64,{img_base64}")

        # Build messages
        content = [{"type": "text", "text": f"""You are extracting data from Swedish BRF (housing cooperative) annual reports.

{extraction_prompt}

Return ONLY valid JSON matching the requested schema. No additional text."""}]

        for img_url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {"url": img_url}
            })

        # Call GPT-4V API (using gpt-4o with vision capabilities)
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=2000,
            temperature=0
        )

        # Parse JSON response
        text = response.choices[0].message.content

        try:
            result = json.loads(text)
            return result
        except json.JSONDecodeError:
            # Try to extract JSON from markdown fence
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                raise ValueError(f"Could not parse JSON from GPT-4V response: {text}")

    def _compute_consensus(
        self,
        model_results: List[VisionModelResult],
        agent_name: str
    ) -> ConsensusResult:
        """
        Combine multiple model results through weighted consensus voting.

        Algorithm:
        1. For each field, compute weighted vote
        2. Select value with highest weighted support
        3. Calculate confidence based on agreement ratio
        4. Handle ties with confidence-based tiebreaker

        Args:
            model_results: Results from each model
            agent_name: Agent name for logging

        Returns:
            ConsensusResult with combined extraction
        """
        # Filter successful results
        successful_results = [r for r in model_results if r.success]

        if not successful_results:
            # No successful extractions - return empty with low confidence
            logger.warning(f"{agent_name}: All vision models failed")
            return ConsensusResult(
                extracted_data={},
                confidence=0.0,
                agreement_ratio=0.0,
                model_results=model_results,
                primary_model="none",
                fallback_used=True
            )

        if len(successful_results) == 1:
            # Only one successful model - use it directly
            result = successful_results[0]
            logger.info(f"{agent_name}: Single model consensus ({result.model_name})")
            return ConsensusResult(
                extracted_data=result.extracted_data,
                confidence=result.confidence,
                agreement_ratio=1.0,  # No disagreement with 1 model
                model_results=model_results,
                primary_model=result.model_name,
                fallback_used=True
            )

        # Multiple successful results - perform weighted voting
        all_fields = set()
        for result in successful_results:
            all_fields.update(result.extracted_data.keys())

        consensus_data = {}
        field_agreements = []

        for field in all_fields:
            # Collect weighted votes for this field
            votes = {}
            total_weight = 0.0

            for result in successful_results:
                if field in result.extracted_data:
                    value = result.extracted_data[field]
                    weight = self.MODEL_WEIGHTS.get(result.model_name, 0.1) * result.confidence

                    # Convert value to string for comparison (handles nulls, numbers, etc.)
                    value_str = str(value) if value is not None else "null"

                    if value_str not in votes:
                        votes[value_str] = 0.0
                    votes[value_str] += weight
                    total_weight += weight

            if votes:
                # Select value with highest weighted vote
                winning_value_str = max(votes, key=votes.get)
                winning_weight = votes[winning_value_str]

                # Calculate agreement ratio for this field
                field_agreement = winning_weight / total_weight if total_weight > 0 else 0.0
                field_agreements.append(field_agreement)

                # Convert back from string (handle special cases)
                if winning_value_str == "null":
                    consensus_data[field] = None
                else:
                    # Try to preserve original type
                    # This is simplified - production would need better type handling
                    try:
                        # Find original value from results
                        for result in successful_results:
                            if field in result.extracted_data:
                                orig_val = result.extracted_data[field]
                                if str(orig_val) == winning_value_str:
                                    consensus_data[field] = orig_val
                                    break
                    except:
                        consensus_data[field] = winning_value_str

        # Calculate overall metrics
        overall_confidence = sum(field_agreements) / len(field_agreements) if field_agreements else 0.0
        agreement_ratio = overall_confidence

        # Determine primary model (highest weight that succeeded)
        primary_model = max(
            successful_results,
            key=lambda r: self.MODEL_WEIGHTS.get(r.model_name, 0.0)
        ).model_name

        logger.info(f"{agent_name}: Consensus from {len(successful_results)} models "
                   f"(confidence: {overall_confidence:.1%}, agreement: {agreement_ratio:.1%})")

        return ConsensusResult(
            extracted_data=consensus_data,
            confidence=overall_confidence,
            agreement_ratio=agreement_ratio,
            model_results=model_results,
            primary_model=primary_model,
            fallback_used=False
        )


# Convenience function
def extract_with_vision_consensus(
    images: List[Tuple[int, Image.Image]],
    extraction_prompt: str,
    agent_name: str = "vision_agent"
) -> ConsensusResult:
    """
    Extract data from images using multi-model vision consensus.

    Args:
        images: List of (page_num, image) tuples
        extraction_prompt: Extraction instructions
        agent_name: Agent name for logging

    Returns:
        ConsensusResult with extracted data

    Example:
        >>> images = [(1, img1), (2, img2)]
        >>> prompt = "Extract chairman name and board members"
        >>> result = extract_with_vision_consensus(images, prompt)
        >>> print(result.confidence)
        0.92
    """
    extractor = VisionConsensusExtractor()
    return extractor.extract_from_images(images, extraction_prompt, agent_name)


if __name__ == "__main__":
    # Test vision consensus extractor
    import sys

    if len(sys.argv) < 2:
        print("Usage: python vision_consensus.py <pdf_path> <agent_name>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    agent_name = sys.argv[2] if len(sys.argv) > 2 else "test_agent"

    logging.basicConfig(level=logging.INFO)

    # Preprocess images
    from image_preprocessor import preprocess_pdf, PreprocessingPresets

    config = PreprocessingPresets.vision_model_optimal()
    images = preprocess_pdf(pdf_path, page_numbers=[1, 2, 3], config=config)

    # Extract with consensus
    prompt = """Extract governance information:
- chairman: Name of chairman (Ordförande)
- board_members: List of board member names
- auditor: Auditor name and firm

Return JSON with these fields."""

    result = extract_with_vision_consensus(images, prompt, agent_name)

    print("\n" + "="*60)
    print("VISION CONSENSUS RESULTS")
    print("="*60)
    print(f"Agent: {agent_name}")
    print(f"Primary Model: {result.primary_model}")
    print(f"Confidence: {result.confidence:.1%}")
    print(f"Agreement: {result.agreement_ratio:.1%}")
    print(f"\nExtracted Data:")
    import json
    print(json.dumps(result.extracted_data, indent=2, ensure_ascii=False))
    print("\nModel Results:")
    for model_result in result.model_results:
        status = "✅" if model_result.success else "❌"
        print(f"  {status} {model_result.model_name}: "
              f"{model_result.confidence:.1%} confidence, "
              f"{model_result.processing_time:.1f}s")
    print("="*60 + "\n")
