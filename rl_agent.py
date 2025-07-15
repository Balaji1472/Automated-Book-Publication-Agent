import json
import re
from collections import defaultdict, Counter
from datetime import datetime
import numpy as np
from typing import Dict, List, Tuple, Optional

class EnhancedRLAgent:
    def __init__(self, file_path="enhanced_rl_state.json"):
        self.file_path = file_path
        self.state = {
            "feedback_history": [],
            "pattern_weights": defaultdict(float),
            "style_preferences": defaultdict(float),
            "focus_area_effectiveness": defaultdict(float),
            "successful_patterns": [],
            "total_feedback": 0,
            "good_feedback_count": 0
        }
        self.load_state()

    def load_state(self):
        """Load the RL agent state from file"""
        try:
            with open(self.file_path, "r") as f:
                loaded_state = json.load(f)
                # Merge with defaults to handle new fields
                for key, value in loaded_state.items():
                    if key in ["pattern_weights", "style_preferences", "focus_area_effectiveness"]:
                        self.state[key] = defaultdict(float, value)
                    else:
                        self.state[key] = value
        except FileNotFoundError:
            self.save_state()

    def save_state(self):
        """Save the RL agent state to file"""
        # Convert defaultdicts to regular dicts for JSON serialization
        save_state = {}
        for key, value in self.state.items():
            if isinstance(value, defaultdict):
                save_state[key] = dict(value)
            else:
                save_state[key] = value
        
        with open(self.file_path, "w") as f:
            json.dump(save_state, f, indent=2)

    def extract_text_patterns(self, text: str) -> Dict[str, float]:
        """Extract writing patterns from text for analysis"""
        patterns = {}
        
        # Sentence structure patterns
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            avg_sentence_length = np.mean([len(s.split()) for s in sentences])
            patterns['avg_sentence_length'] = avg_sentence_length
            patterns['sentence_variety'] = np.std([len(s.split()) for s in sentences])
            
            # dialogue detection
            dialogue_count = len(re.findall(r'"[^"]*"', text))
            patterns['dialogue_density'] = dialogue_count / len(sentences) if sentences else 0
            
            # descriptive language
            adjectives = len(re.findall(r'\b(?:beautiful|vivid|mysterious|elegant|powerful|gentle|fierce|ancient|modern|complex)\b', text.lower()))
            patterns['descriptive_density'] = adjectives / len(text.split()) if text.split() else 0
            
            # transition words
            transitions = len(re.findall(r'\b(?:however|therefore|meanwhile|suddenly|finally|moreover|consequently|furthermore)\b', text.lower()))
            patterns['transition_density'] = transitions / len(sentences) if sentences else 0
            
            # paragraph structure
            paragraphs = text.split('\n\n')
            patterns['avg_paragraph_length'] = np.mean([len(p.split()) for p in paragraphs if p.strip()])
            
            # Reading complexity (simplified)
            complex_words = len(re.findall(r'\b\w{8,}\b', text))
            patterns['complexity_score'] = complex_words / len(text.split()) if text.split() else 0
        
        return patterns

    def update(self, rating: str, output: str, style_preference: str = "modern", 
               focus_areas: List[str] = None, metadata: Dict = None):
        """Update the RL agent with user feedback and learn from patterns"""
        
        if focus_areas is None:
            focus_areas = []
        
        # Extract patterns from the output
        text_patterns = self.extract_text_patterns(output)
        
        # Create feedback record
        feedback_record = {
            "timestamp": datetime.now().isoformat(),
            "rating": rating,
            "output_hash": hash(output.strip()),
            "style_preference": style_preference,
            "focus_areas": focus_areas,
            "text_patterns": text_patterns,
            "word_count": len(output.split()),
            "metadata": metadata or {}
        }
        
        # Update state
        self.state["feedback_history"].append(feedback_record)
        self.state["total_feedback"] += 1
        
        # Rating-based learning
        rating_weight = 1.0 if rating == "Good" else -0.5
        
        if rating == "Good":
            self.state["good_feedback_count"] += 1
            
            # Learn from successful patterns
            for pattern_name, pattern_value in text_patterns.items():
                self.state["pattern_weights"][pattern_name] += rating_weight * pattern_value
            
            # Learn style preferences
            self.state["style_preferences"][style_preference] += rating_weight
            
            # Learn focus area effectiveness
            for area in focus_areas:
                self.state["focus_area_effectiveness"][area] += rating_weight
            
            # Store successful patterns for later analysis
            self.state["successful_patterns"].append({
                "patterns": text_patterns,
                "style": style_preference,
                "focus_areas": focus_areas,
                "timestamp": datetime.now().isoformat()
            })
        
        else:  # Bad rating
            # Reduce weight for unsuccessful patterns
            for pattern_name, pattern_value in text_patterns.items():
                self.state["pattern_weights"][pattern_name] += rating_weight * pattern_value * 0.5
            
            self.state["style_preferences"][style_preference] += rating_weight * 0.5
            
            for area in focus_areas:
                self.state["focus_area_effectiveness"][area] += rating_weight * 0.5
        
        # Keep only recent successful patterns (last 50)
        if len(self.state["successful_patterns"]) > 50:
            self.state["successful_patterns"] = self.state["successful_patterns"][-50:]
        
        # Keep only recent feedback history (last 100)
        if len(self.state["feedback_history"]) > 100:
            self.state["feedback_history"] = self.state["feedback_history"][-100:]
        
        self.save_state()

    def get_smart_suggestions(self) -> Dict[str, any]:
        """Get intelligent suggestions based on learned patterns"""
        suggestions = {
            "recommended_style": "modern",
            "recommended_focus_areas": ["grammar", "clarity", "flow"],
            "confidence_score": 0.0,
            "success_rate": 0.0,
            "total_feedback": self.state["total_feedback"],
            "learning_insights": []
        }
        
        if self.state["total_feedback"] == 0:
            return suggestions
        
        # Calculate success rate
        suggestions["success_rate"] = (self.state["good_feedback_count"] / self.state["total_feedback"]) * 100
        
        # Get best style preference
        if self.state["style_preferences"]:
            best_style = max(self.state["style_preferences"].items(), key=lambda x: x[1])
            if best_style[1] > 0:
                suggestions["recommended_style"] = best_style[0]
                suggestions["confidence_score"] = min(best_style[1] / 5.0, 1.0)
        
        # Get best focus areas (top 3)
        if self.state["focus_area_effectiveness"]:
            effective_areas = sorted(self.state["focus_area_effectiveness"].items(), 
                                   key=lambda x: x[1], reverse=True)
            positive_areas = [area for area, weight in effective_areas if weight > 0]
            if positive_areas:
                suggestions["recommended_focus_areas"] = positive_areas[:3]
        
        # Generate insights
        insights = []
        
        # Style insights
        if self.state["style_preferences"]:
            style_items = sorted(self.state["style_preferences"].items(), 
                               key=lambda x: x[1], reverse=True)
            if style_items[0][1] > 0:
                insights.append(f"'{style_items[0][0]}' style performs best (weight: {style_items[0][1]:.1f})")
        
        # Focus area insights
        if self.state["focus_area_effectiveness"]:
            focus_items = sorted(self.state["focus_area_effectiveness"].items(), 
                               key=lambda x: x[1], reverse=True)
            top_focus = [f"{area} ({weight:.1f})" for area, weight in focus_items[:3] if weight > 0]
            if top_focus:
                insights.append(f"Most effective focus areas: {', '.join(top_focus)}")
        
        # Pattern insights
        if self.state["pattern_weights"]:
            pattern_items = sorted(self.state["pattern_weights"].items(), 
                                 key=lambda x: x[1], reverse=True)
            if pattern_items[0][1] > 0:
                insights.append(f"Successful pattern: {pattern_items[0][0]} (weight: {pattern_items[0][1]:.1f})")
        
        suggestions["learning_insights"] = insights
        return suggestions

    def get_adaptive_prompt_instructions(self, agent_type: str = "writer") -> str:
        """Generate adaptive prompt instructions based on learned patterns"""
        
        if self.state["total_feedback"] < 3:  # Need minimum feedback to learn
            return ""
        
        instructions = []
        
        # Style-based instructions
        if self.state["style_preferences"]:
            best_style = max(self.state["style_preferences"].items(), key=lambda x: x[1])
            if best_style[1] > 0:
                instructions.append(f"Focus on {best_style[0]} writing style as it has shown high user satisfaction.")
        
        # Pattern-based instructions
        if self.state["pattern_weights"]:
            # Get top positive patterns
            positive_patterns = {k: v for k, v in self.state["pattern_weights"].items() if v > 0}
            if positive_patterns:
                sorted_patterns = sorted(positive_patterns.items(), key=lambda x: x[1], reverse=True)
                
                top_pattern = sorted_patterns[0]
                if top_pattern[0] == "avg_sentence_length":
                    if top_pattern[1] > 2:
                        instructions.append("Use varied sentence lengths with a preference for medium-length sentences.")
                elif top_pattern[0] == "dialogue_density":
                    if top_pattern[1] > 1:
                        instructions.append("Include natural dialogue when appropriate to enhance engagement.")
                elif top_pattern[0] == "descriptive_density":
                    if top_pattern[1] > 1:
                        instructions.append("Use rich, descriptive language to create vivid imagery.")
                elif top_pattern[0] == "transition_density":
                    if top_pattern[1] > 1:
                        instructions.append("Use smooth transitions between ideas and paragraphs.")
        
        # Focus area instructions
        if self.state["focus_area_effectiveness"]:
            effective_areas = {k: v for k, v in self.state["focus_area_effectiveness"].items() if v > 0}
            if effective_areas:
                sorted_areas = sorted(effective_areas.items(), key=lambda x: x[1], reverse=True)
                top_areas = [area for area, weight in sorted_areas[:3]]
                
                if agent_type == "writer":
                    if "engagement" in top_areas:
                        instructions.append("Prioritize reader engagement and compelling narrative flow.")
                    if "style" in top_areas:
                        instructions.append("Pay special attention to consistent and polished writing style.")
                elif agent_type == "reviewer":
                    if "grammar" in top_areas:
                        instructions.append("Thoroughly review grammar and punctuation errors.")
                    if "clarity" in top_areas:
                        instructions.append("Ensure exceptional clarity and readability.")
                    if "flow" in top_areas:
                        instructions.append("Optimize paragraph and sentence flow for smooth reading.")
        
        # Success rate based instructions
        success_rate = (self.state["good_feedback_count"] / self.state["total_feedback"]) * 100
        if success_rate > 70:
            instructions.append("Continue with the current approach as it's achieving high user satisfaction.")
        elif success_rate < 50:
            instructions.append("Focus on fundamental quality improvements based on user feedback patterns.")
        
        return "\n".join(f"- {instruction}" for instruction in instructions)

    def get_learning_stats(self) -> Dict:
        """Get comprehensive learning statistics"""
        stats = {
            "total_feedback": self.state["total_feedback"],
            "good_feedback": self.state["good_feedback_count"],
            "success_rate": 0.0,
            "learning_patterns": len(self.state["successful_patterns"]),
            "style_distribution": dict(self.state["style_preferences"]),
            "focus_effectiveness": dict(self.state["focus_area_effectiveness"]),
            "recent_improvements": []
        }
        
        if self.state["total_feedback"] > 0:
            stats["success_rate"] = (self.state["good_feedback_count"] / self.state["total_feedback"]) * 100
        
        # Recent improvements (last 10 feedback items)
        recent_feedback = self.state["feedback_history"][-10:]
        if len(recent_feedback) >= 5:
            recent_good = sum(1 for f in recent_feedback if f["rating"] == "Good")
            recent_success_rate = (recent_good / len(recent_feedback)) * 100
            stats["recent_improvements"] = [
                f"Recent success rate: {recent_success_rate:.1f}%",
                f"Learning from {len(recent_feedback)} recent interactions"
            ]
        
        return stats

    def reset_learning(self):
        """Reset all learning data (for testing/debugging)"""
        self.state = {
            "feedback_history": [],
            "pattern_weights": defaultdict(float),
            "style_preferences": defaultdict(float),
            "focus_area_effectiveness": defaultdict(float),
            "successful_patterns": [],
            "total_feedback": 0,
            "good_feedback_count": 0
        }
        self.save_state()

# Create global instance
rl_agent = EnhancedRLAgent()