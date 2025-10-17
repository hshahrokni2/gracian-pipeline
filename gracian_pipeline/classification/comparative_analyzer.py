"""
Layer 6: Comparative Intelligence

Compares individual BRF metrics against population statistics for relative intelligence.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import math


@dataclass
class ComparisonResult:
    """Result of comparing a metric to population."""
    metric_name: str
    value: float
    percentile_rank: Optional[float] = None  # 0-100
    z_score: Optional[float] = None  # Standard deviations from mean
    category: str = "INSUFFICIENT_DATA"  # Well Above, Above, Average, Below, Well Below
    emoji: str = "❓"
    narrative: str = ""
    population_stats: Dict[str, Any] = field(default_factory=dict)


class ComparativeAnalyzer:
    """
    Compares individual BRF metrics against population statistics.

    NOTE: This is a framework implementation. Full functionality requires
    population statistics database built from 27K PDFs.
    """

    def __init__(self):
        """Initialize with mock population statistics for demonstration."""
        # TODO: Replace with actual population statistics from database
        self.pop_stats = self._mock_population_stats()

    def _mock_population_stats(self) -> Dict:
        """
        Mock population statistics for demonstration.

        In production, this would be loaded from database after processing 27K PDFs.
        """
        return {
            'soliditet_pct': {
                'data_availability': 0.94,
                'mean': 68.5,
                'median': 71.2,
                'std_dev': 18.3,
                'percentiles': {10: 42.1, 25: 58.3, 50: 71.2, 75: 82.5, 90: 89.7},
                'min': 12.3,
                'max': 98.2,
                'sample_size': 25380
            },
            'total_debt_per_sqm': {
                'data_availability': 0.89,
                'mean': 13200,
                'median': 11800,
                'std_dev': 5400,
                'percentiles': {10: 5200, 25: 8100, 50: 11800, 75: 16500, 90: 21300},
                'min': 0,
                'max': 42000,
                'sample_size': 24030
            },
            'monthly_fee_per_sqm': {
                'data_availability': 0.96,
                'mean': 54.8,
                'median': 52.0,
                'std_dev': 18.2,
                'percentiles': {10: 32.5, 25: 42.0, 50: 52.0, 75: 64.0, 90: 78.5},
                'min': 18.0,
                'max': 145.0,
                'sample_size': 25920
            },
        }

    def calculate_percentile_rank(self, metric_name: str, value: float) -> Optional[float]:
        """
        Calculate where this value falls in population distribution (0-100).

        Returns:
            Percentile rank: What % of BRFs have lower values
        """
        stats = self.pop_stats.get(metric_name)
        if not stats:
            return None

        percentiles = stats['percentiles']

        # Simple linear interpolation between percentile points
        if value <= percentiles[10]:
            return (value / percentiles[10]) * 10
        elif value <= percentiles[25]:
            return 10 + ((value - percentiles[10]) / (percentiles[25] - percentiles[10])) * 15
        elif value <= percentiles[50]:
            return 25 + ((value - percentiles[25]) / (percentiles[50] - percentiles[25])) * 25
        elif value <= percentiles[75]:
            return 50 + ((value - percentiles[50]) / (percentiles[75] - percentiles[50])) * 25
        elif value <= percentiles[90]:
            return 75 + ((value - percentiles[75]) / (percentiles[90] - percentiles[75])) * 15
        else:
            if value >= stats['max']:
                return 100
            return 90 + ((value - percentiles[90]) / (stats['max'] - percentiles[90])) * 10

    def calculate_z_score(self, metric_name: str, value: float) -> Optional[float]:
        """
        Calculate standard deviation distance from mean.

        Returns:
            Z-score: How many standard deviations from mean
        """
        stats = self.pop_stats.get(metric_name)
        if not stats:
            return None

        return (value - stats['mean']) / stats['std_dev']

    def compare_to_population(
        self,
        metric_name: str,
        value: float
    ) -> ComparisonResult:
        """
        Full comparison analysis of a single metric.

        Returns:
            ComparisonResult with percentile, category, and narrative
        """
        percentile = self.calculate_percentile_rank(metric_name, value)
        z_score = self.calculate_z_score(metric_name, value)
        stats = self.pop_stats.get(metric_name)

        if not stats or percentile is None:
            return ComparisonResult(
                metric_name=metric_name,
                value=value,
                category="INSUFFICIENT_DATA",
                emoji="❓",
                narrative=f"Population data not available for {metric_name}"
            )

        # Categorize
        if percentile >= 90:
            category = "Well Above Average"
            emoji = "🔥"
        elif percentile >= 75:
            category = "Above Average"
            emoji = "📈"
        elif percentile >= 25:
            category = "Average"
            emoji = "➡️"
        elif percentile >= 10:
            category = "Below Average"
            emoji = "📉"
        else:
            category = "Well Below Average"
            emoji = "⚠️"

        # Generate narrative
        narrative = self._generate_narrative(metric_name, value, percentile, stats)

        return ComparisonResult(
            metric_name=metric_name,
            value=value,
            percentile_rank=round(percentile, 1),
            z_score=round(z_score, 2) if z_score else None,
            category=category,
            emoji=emoji,
            narrative=narrative,
            population_stats={
                'median': stats['median'],
                'mean': stats['mean'],
                'sample_size': stats['sample_size']
            }
        )

    def _generate_narrative(
        self,
        metric_name: str,
        value: float,
        percentile: float,
        stats: Dict
    ) -> str:
        """Generate human-readable comparison narrative."""
        median = stats['median']
        diff_pct = ((value - median) / median) * 100 if median != 0 else 0

        if abs(diff_pct) < 5:
            return f"Your {metric_name} of {value:.1f} is typical " \
                   f"(within 5% of median {median:.1f}). " \
                   f"You're in the {percentile:.0f}th percentile."

        elif diff_pct > 0:
            return f"Your {metric_name} of {value:.1f} is {diff_pct:.0f}% above " \
                   f"the typical BRF (median: {median:.1f}). " \
                   f"You rank in the {percentile:.0f}th percentile - " \
                   f"higher than {percentile:.0f}% of BRFs."

        else:
            return f"Your {metric_name} of {value:.1f} is {abs(diff_pct):.0f}% below " \
                   f"the typical BRF (median: {median:.1f}). " \
                   f"You rank in the {percentile:.0f}th percentile - " \
                   f"lower than {100-percentile:.0f}% of BRFs."

    def compare_multiple_metrics(
        self,
        data: Dict[str, float]
    ) -> Dict[str, ComparisonResult]:
        """
        Compare multiple metrics at once.

        Args:
            data: Dictionary of {metric_name: value}

        Returns:
            Dictionary of {metric_name: ComparisonResult}
        """
        results = {}
        for metric_name, value in data.items():
            if metric_name in self.pop_stats:
                results[metric_name] = self.compare_to_population(metric_name, value)

        return results
