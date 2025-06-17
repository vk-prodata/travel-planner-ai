"""
Test comprehensive entertainment preference prompt logic
"""
import pytest
from travel_planner_ai.backend.ai_client import AIClient


class TestEntertainmentPreferencePrompts:
    """Test the comprehensive entertainment preference prompt system"""
    
    @pytest.fixture
    def ai_client(self):
        """Create AI client instance for testing"""
        return AIClient(api_key="test-key", provider="openai")
    
    def test_outdoor_preference_prompts(self, ai_client):
        """Test outdoor preference generates appropriate prompt logic"""
        preferences = ['outdoor']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert len(context['activities_focus']) == 1
        assert 'OUTDOOR ADVENTURES' in context['activities_focus'][0]
        assert 'nature-based activities' in context['activities_focus'][0]
        
        assert 'OUTDOOR: Weather-dependent activities' in context['selection_criteria'][0]
        assert 'OUTDOOR: Schedule outdoor activities' in context['timing_constraints'][0]
    
    def test_cultural_preference_prompts(self, ai_client):
        """Test cultural preference generates appropriate prompt logic"""
        preferences = ['cultural']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'CULTURAL IMMERSION' in context['activities_focus'][0]
        assert 'authentic local culture' in context['activities_focus'][0]
        assert 'CULTURAL: Educational value' in context['selection_criteria'][0]
        assert 'museum hours' in context['timing_constraints'][0]
    
    def test_family_friendly_preference_prompts(self, ai_client):
        """Test family-friendly preference generates appropriate prompt logic"""
        preferences = ['family-friendly']
        args = {'children': 2, 'adults': 2}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'FAMILY EXPERIENCES' in context['activities_focus'][0]
        assert 'Safe, engaging activities' in context['activities_focus'][0]
        assert 'FAMILY-FRIENDLY: Safety' in context['selection_criteria'][0]
        assert len(context['special_instructions']) == 1
        assert 'FAMILY-FRIENDLY PRIORITY' in context['special_instructions'][0]
        assert '2 adults' in context['special_instructions'][0]
    
    def test_shopping_preference_prompts(self, ai_client):
        """Test shopping preference generates appropriate prompt logic"""
        preferences = ['shopping']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'SHOPPING & MARKETS' in context['activities_focus'][0]
        assert 'Local crafts' in context['activities_focus'][0]
        assert 'SHOPPING: Authenticity' in context['selection_criteria'][0]
        assert 'Market operating hours' in context['timing_constraints'][0]
    
    def test_adventure_preference_prompts(self, ai_client):
        """Test adventure preference generates appropriate prompt logic"""
        preferences = ['adventure']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'ADVENTURE SEEKING' in context['activities_focus'][0]
        assert 'Thrilling, active experiences' in context['activities_focus'][0]
        assert 'ADVENTURE: Physical challenge level' in context['selection_criteria'][0]
        assert 'Weather conditions' in context['timing_constraints'][0]
    
    def test_nightlife_preference_prompts(self, ai_client):
        """Test nightlife preference generates appropriate prompt logic"""
        preferences = ['nightlife']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'EVENING ENTERTAINMENT' in context['activities_focus'][0]
        assert 'After-dark activities' in context['activities_focus'][0]
        assert 'NIGHTLIFE: Local atmosphere' in context['selection_criteria'][0]
        assert 'Evening and night hours' in context['timing_constraints'][0]
    
    def test_must_see_preference_prompts(self, ai_client):
        """Test must-see preference generates appropriate prompt logic"""
        preferences = ['must-see']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'ICONIC ATTRACTIONS' in context['activities_focus'][0]
        assert 'Essential landmarks' in context['activities_focus'][0]
        assert 'MUST-SEE: Universal recognition' in context['selection_criteria'][0]
        assert 'Peak visiting hours' in context['timing_constraints'][0]
    
    def test_relax_preference_prompts(self, ai_client):
        """Test relax preference generates appropriate prompt logic"""
        preferences = ['relax']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'RELAXATION & WELLNESS' in context['activities_focus'][0]
        assert 'Peaceful, rejuvenating' in context['activities_focus'][0]
        assert 'RELAX: Peaceful atmosphere' in context['selection_criteria'][0]
        assert 'Quieter hours' in context['timing_constraints'][0]
    
    def test_hidden_gems_preference_prompts(self, ai_client):
        """Test hidden-gems preference generates appropriate prompt logic"""
        preferences = ['hidden-gems']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'LOCAL SECRETS' in context['activities_focus'][0]
        assert 'where locals go' in context['activities_focus'][0]
        assert 'HIDDEN-GEMS: Local ownership' in context['selection_criteria'][0]
        assert len(context['special_instructions']) == 1
        assert 'HIDDEN GEMS - LOCAL FOCUS' in context['special_instructions'][0]
    
    def test_photoshoot_preference_prompts(self, ai_client):
        """Test photoshoot preference generates appropriate prompt logic"""
        preferences = ['photoshoot']
        args = {
            'photoshootSettings': {
                'mode': 'nature'
            }
        }
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        assert 'PHOTOGRAPHY OPPORTUNITIES' in context['activities_focus'][0]
        assert 'visual appeal' in context['activities_focus'][0]
        assert 'PHOTOSHOOT: Visual appeal' in context['selection_criteria'][0]
        assert len(context['special_instructions']) == 1
        assert 'PHOTOSHOOT MODE ACTIVATED' in context['special_instructions'][0]
        assert 'NATURE PHOTOGRAPHY FOCUS' in context['special_instructions'][0]
    
    def test_multiple_preferences_combination(self, ai_client):
        """Test multiple preferences are properly combined"""
        preferences = ['outdoor', 'family-friendly', 'cultural']
        args = {'children': 1, 'adults': 2}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        # Should have 3 activity focuses
        assert len(context['activities_focus']) == 3
        assert any('OUTDOOR ADVENTURES' in focus for focus in context['activities_focus'])
        assert any('FAMILY EXPERIENCES' in focus for focus in context['activities_focus'])
        assert any('CULTURAL IMMERSION' in focus for focus in context['activities_focus'])
        
        # Should have 3 selection criteria
        assert len(context['selection_criteria']) == 3
        assert any('OUTDOOR:' in criteria for criteria in context['selection_criteria'])
        assert any('FAMILY-FRIENDLY:' in criteria for criteria in context['selection_criteria'])
        assert any('CULTURAL:' in criteria for criteria in context['selection_criteria'])
        
        # Should have family-friendly special instruction
        assert len(context['special_instructions']) == 1
        assert 'FAMILY-FRIENDLY PRIORITY' in context['special_instructions'][0]
    
    def test_unknown_preference_ignored(self, ai_client):
        """Test unknown preferences are ignored gracefully"""
        preferences = ['outdoor', 'unknown-preference', 'cultural']
        args = {}
        
        context = ai_client._build_entertainment_preference_prompts(preferences, args)
        
        # Should only have 2 activity focuses (outdoor and cultural)
        assert len(context['activities_focus']) == 2
        assert any('OUTDOOR ADVENTURES' in focus for focus in context['activities_focus'])
        assert any('CULTURAL IMMERSION' in focus for focus in context['activities_focus'])
    
    def test_comprehensive_context_integration(self, ai_client):
        """Test that comprehensive context is properly integrated in _build_preferences_context"""
        args = {
            'entertainmentPreferences': ['outdoor', 'family-friendly'],
            'children': 2,
            'adults': 2
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert context['preferences_text'] == 'outdoor, family-friendly'
        assert 'ACTIVITY FOCUS:' in context['comprehensive_context']
        assert 'OUTDOOR ADVENTURES' in context['comprehensive_context']
        assert 'FAMILY EXPERIENCES' in context['comprehensive_context']
        assert 'SELECTION CRITERIA:' in context['comprehensive_context']
        assert 'TIMING CONSIDERATIONS:' in context['comprehensive_context']
        assert 'FAMILY-FRIENDLY PRIORITY' in context['local_focus']
    
    def test_refresh_activity_uses_preference_system(self, ai_client):
        """Test that refresh_activity_suggestion uses the new preference system"""
        # This is more of an integration test to ensure the method uses the new system
        # We can't test the full async method easily, but we can test the preference parsing logic
        
        custom_preferences = "outdoor, hidden-gems"
        parsed_preferences = [pref.strip().lower() for pref in custom_preferences.lower().split(',')]
        
        assert 'outdoor' in parsed_preferences
        assert 'hidden-gems' in parsed_preferences
        
        # Test that the preference system handles these correctly
        context = ai_client._build_entertainment_preference_prompts(parsed_preferences, {})
        
        assert len(context['activities_focus']) == 2
        assert len(context['special_instructions']) == 1  # hidden-gems special instruction
        assert 'HIDDEN GEMS - LOCAL FOCUS' in context['special_instructions'][0] 