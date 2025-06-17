import pytest
from unittest.mock import AsyncMock, MagicMock
from travel_planner_ai.backend.ai_client import AIClient


class TestPhotoshootAIIntegration:
    """Test photoshoot feature integration with AI client"""
    
    @pytest.fixture
    def ai_client(self):
        """Create AI client instance for testing"""
        return AIClient(api_key="test-key", provider="openai")
    
    def test_build_preferences_context_with_photoshoot_nature(self, ai_client):
        """Test that nature photoshoot mode generates correct context"""
        args = {
            'entertainmentPreferences': ['photoshoot', 'outdoor'],
            'photoshootSettings': {
                'mode': 'nature'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'photoshoot, outdoor' in context['preferences_text']
        assert 'PHOTOSHOOT MODE ACTIVATED' in context['photoshoot_context']
        assert 'NATURE PHOTOGRAPHY FOCUS' in context['photoshoot_context']
        assert 'Landscapes with dramatic lighting' in context['photoshoot_context']
        assert 'golden hour' in context['photoshoot_context']
    
    def test_build_preferences_context_with_photoshoot_architecture(self, ai_client):
        """Test that architecture photoshoot mode generates correct context"""
        args = {
            'entertainmentPreferences': ['photoshoot', 'cultural'],
            'photoshootSettings': {
                'mode': 'architecture'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'ARCHITECTURE PHOTOGRAPHY FOCUS' in context['photoshoot_context']
        assert 'Historic buildings with unique architectural details' in context['photoshoot_context']
        assert 'morning for clean shadows, afternoon for side lighting' in context['photoshoot_context']
        assert 'end 1 hour before sunset' in context['photoshoot_context']
    
    def test_build_preferences_context_with_photoshoot_local(self, ai_client):
        """Test that local photoshoot mode generates correct context"""
        args = {
            'entertainmentPreferences': ['photoshoot'],
            'photoshootSettings': {
                'mode': 'local'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'LOCAL LIFESTYLE PHOTOGRAPHY FOCUS' in context['photoshoot_context']
        assert 'Candid street photography opportunities' in context['photoshoot_context']
        assert 'morning for opening activities, midday for bustling life' in context['photoshoot_context']
        assert 'end 1 hour before sunset' in context['photoshoot_context']
    
    def test_build_preferences_context_with_photoshoot_kids(self, ai_client):
        """Test that kids photoshoot mode generates correct context"""
        args = {
            'entertainmentPreferences': ['photoshoot', 'family-friendly'],
            'photoshootSettings': {
                'mode': 'kids'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'FAMILY PHOTOGRAPHY FOCUS' in context['photoshoot_context']
        assert 'Kid-friendly locations with photogenic' in context['photoshoot_context']
        assert 'natural poses and genuine expressions' in context['photoshoot_context']
    
    def test_build_preferences_context_with_photoshoot_wildlife(self, ai_client):
        """Test that wildlife photoshoot mode generates correct context"""
        args = {
            'entertainmentPreferences': ['photoshoot', 'outdoor'],
            'photoshootSettings': {
                'mode': 'wildlife'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'WILDLIFE PHOTOGRAPHY FOCUS' in context['photoshoot_context']
        assert 'Natural habitats with wildlife viewing' in context['photoshoot_context']
        assert 'early morning for dawn activity, afternoon for feeding' in context['photoshoot_context']
        assert 'end 1 hour before sunset' in context['photoshoot_context']
        assert 'Ethical wildlife viewing locations' in context['photoshoot_context']
    
    def test_build_preferences_context_with_photoshoot_insta_blogger(self, ai_client):
        """Test that insta-blogger photoshoot mode generates correct context"""
        args = {
            'entertainmentPreferences': ['photoshoot'],
            'photoshootSettings': {
                'mode': 'insta-blogger',
                'instagramHandle': '@test_photographer'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'INSTAGRAM BLOGGER STYLE - Following @test_photographer' in context['photoshoot_context']
        assert 'Research and emulate the aesthetic' in context['photoshoot_context']
        assert 'Instagram-worthy spots with high visual impact' in context['photoshoot_context']
    
    def test_build_preferences_context_without_photoshoot(self, ai_client):
        """Test that no photoshoot context is generated when photoshoot is not selected"""
        args = {
            'entertainmentPreferences': ['outdoor', 'cultural'],
            'photoshootSettings': {}
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert context['photoshoot_context'] == ""
        assert 'PHOTOSHOOT MODE' not in context.get('photoshoot_context', '')
    
    def test_build_preferences_context_photoshoot_without_mode(self, ai_client):
        """Test that photoshoot preference without mode doesn't generate specific context"""
        args = {
            'entertainmentPreferences': ['photoshoot'],
            'photoshootSettings': {}
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert context['photoshoot_context'] == ""
    
    def test_build_preferences_context_with_hidden_gems_and_photoshoot(self, ai_client):
        """Test that both hidden gems and photoshoot contexts are generated"""
        args = {
            'entertainmentPreferences': ['photoshoot', 'hidden-gems'],
            'photoshootSettings': {
                'mode': 'nature'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert 'HIDDEN GEMS - LOCAL FOCUS' in context['local_focus']
        assert 'PHOTOSHOOT MODE ACTIVATED' in context['photoshoot_context']
        assert 'NATURE PHOTOGRAPHY FOCUS' in context['photoshoot_context']
    
    def test_generate_prompt_includes_photoshoot_context(self, ai_client):
        """Test that the generated prompt includes photoshoot context"""
        args = {
            'startDate': '2024-07-01',
            'endDate': '2024-07-03',
            'destination': 'Paris',
            'budgetLevel': 'mid-range',
            'entertainmentPreferences': ['photoshoot'],
            'photoshootSettings': {
                'mode': 'architecture'
            }
        }
        
        prompt = ai_client._generate_prompt(args)
        
        assert 'PHOTOSHOOT MODE ACTIVATED' in prompt
        assert 'ARCHITECTURE PHOTOGRAPHY FOCUS' in prompt
        assert 'Historic buildings with unique architectural details' in prompt
        assert 'morning for clean shadows, afternoon for side lighting' in prompt
        assert 'TIMING CONSTRAINT: Photoshoot activities can be scheduled at ANY time of the day but MUST end at least 1 hour before sunset' in prompt
    
    def test_instagram_handle_validation(self, ai_client):
        """Test that Instagram handle is properly included in context"""
        args = {
            'entertainmentPreferences': ['photoshoot'],
            'photoshootSettings': {
                'mode': 'insta-blogger',
                'instagramHandle': '@elenakudry_usa'
            }
        }
        
        context = ai_client._build_preferences_context(args)
        
        assert '@elenakudry_usa' in context['photoshoot_context']
        assert 'Following @elenakudry_usa' in context['photoshoot_context'] 