import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';

export interface Suggestion {
  id: string;
  text: string;
  icon?: string;
  category: 'weather' | 'news' | 'calendar' | 'general' | 'voice';
  description?: string;
}

@Component({
  selector: 'app-suggestions',
  templateUrl: './suggestions.component.html',
  styleUrls: ['./suggestions.component.scss']
})
export class SuggestionsComponent implements OnInit {
  @Input() isLoading: boolean = false;
  @Input() disabled: boolean = false;
  @Output() suggestionSelected = new EventEmitter<string>();

  suggestions: Suggestion[] = [];
  filteredSuggestions: Suggestion[] = [];
  selectedCategory: string = 'all';
  searchTerm: string = '';

  categories = [
    { id: 'all', name: 'All', icon: 'apps' },
    { id: 'weather', name: 'Weather', icon: 'wb_sunny' },
    { id: 'news', name: 'News', icon: 'newspaper' },
    { id: 'calendar', name: 'Calendar', icon: 'event' },
    { id: 'general', name: 'General', icon: 'chat' },
    { id: 'voice', name: 'Voice', icon: 'mic' }
  ];

  private defaultSuggestions: Suggestion[] = [
    // Weather suggestions
    {
      id: 'weather-current',
      text: 'What\'s the current weather?',
      icon: 'wb_sunny',
      category: 'weather',
      description: 'Get current weather conditions'
    },
    {
      id: 'weather-forecast',
      text: 'Show me the 5-day forecast',
      icon: 'cloud',
      category: 'weather',
      description: 'Get extended weather forecast'
    },
    {
      id: 'weather-location',
      text: 'Weather in New York',
      icon: 'location_on',
      category: 'weather',
      description: 'Get weather for a specific city'
    },

    // News suggestions
    {
      id: 'news-headlines',
      text: 'Show me the latest news',
      icon: 'newspaper',
      category: 'news',
      description: 'Get current news headlines'
    },
    {
      id: 'news-technology',
      text: 'Technology news',
      icon: 'computer',
      category: 'news',
      description: 'Get tech-related news'
    },
    {
      id: 'news-business',
      text: 'Business news updates',
      icon: 'business',
      category: 'news',
      description: 'Get business and finance news'
    },

    // Calendar suggestions
    {
      id: 'calendar-today',
      text: 'What\'s on my calendar today?',
      icon: 'today',
      category: 'calendar',
      description: 'View today\'s events'
    },
    {
      id: 'calendar-week',
      text: 'Show my schedule for this week',
      icon: 'date_range',
      category: 'calendar',
      description: 'View weekly schedule'
    },
    {
      id: 'calendar-create',
      text: 'Schedule a meeting for tomorrow',
      icon: 'event_note',
      category: 'calendar',
      description: 'Create a new calendar event'
    },

    // General suggestions
    {
      id: 'general-help',
      text: 'What can you help me with?',
      icon: 'help',
      category: 'general',
      description: 'Learn about available features'
    },
    {
      id: 'general-explain',
      text: 'Explain artificial intelligence',
      icon: 'psychology',
      category: 'general',
      description: 'Get explanations on topics'
    },
    {
      id: 'general-translate',
      text: 'Translate "Hello" to Spanish',
      icon: 'translate',
      category: 'general',
      description: 'Translation assistance'
    },

    // Voice suggestions
    {
      id: 'voice-test',
      text: 'Test voice recognition',
      icon: 'mic',
      category: 'voice',
      description: 'Try voice input feature'
    },
    {
      id: 'voice-commands',
      text: 'What voice commands are available?',
      icon: 'record_voice_over',
      category: 'voice',
      description: 'Learn voice commands'
    },
    {
      id: 'voice-read',
      text: 'Read the last message aloud',
      icon: 'volume_up',
      category: 'voice',
      description: 'Use text-to-speech'
    }
  ];

  ngOnInit(): void {
    this.loadSuggestions();
    this.filterSuggestions();
  }

  /**
   * Load suggestions (could be from a service in the future)
   */
  private loadSuggestions(): void {
    this.suggestions = [...this.defaultSuggestions];
    
    // Add dynamic suggestions based on context
    this.addContextualSuggestions();
  }

  /**
   * Add contextual suggestions based on current state
   */
  private addContextualSuggestions(): void {
    const hour = new Date().getHours();
    
    // Time-based suggestions
    if (hour >= 6 && hour <= 10) {
      this.suggestions.unshift({
        id: 'morning-weather',
        text: 'Good morning! How\'s the weather today?',
        icon: 'wb_sunny',
        category: 'weather',
        description: 'Morning weather check'
      });
    } else if (hour >= 17 && hour <= 21) {
      this.suggestions.unshift({
        id: 'evening-news',
        text: 'What happened in the news today?',
        icon: 'newspaper',
        category: 'news',
        description: 'Evening news summary'
      });
    }

    // Day-based suggestions
    const dayOfWeek = new Date().getDay();
    if (dayOfWeek === 1) { // Monday
      this.suggestions.unshift({
        id: 'monday-schedule',
        text: 'What\'s my schedule for this week?',
        icon: 'event',
        category: 'calendar',
        description: 'Weekly planning'
      });
    } else if (dayOfWeek === 5) { // Friday
      this.suggestions.unshift({
        id: 'friday-weather',
        text: 'Weekend weather forecast',
        icon: 'beach_access',
        category: 'weather',
        description: 'Weekend planning'
      });
    }
  }

  /**
   * Filter suggestions based on category and search term
   */
  filterSuggestions(): void {
    let filtered = this.suggestions;

    // Filter by category
    if (this.selectedCategory !== 'all') {
      filtered = filtered.filter(s => s.category === this.selectedCategory);
    }

    // Filter by search term
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(s => 
        s.text.toLowerCase().includes(term) ||
        s.description?.toLowerCase().includes(term) ||
        s.category.toLowerCase().includes(term)
      );
    }

    this.filteredSuggestions = filtered;
  }

  /**
   * Handle category selection
   */
  onCategorySelected(categoryId: string): void {
    this.selectedCategory = categoryId;
    this.filterSuggestions();
  }

  /**
   * Handle search input
   */
  onSearchInput(searchTerm: string): void {
    this.searchTerm = searchTerm;
    this.filterSuggestions();
  }

  /**
   * Handle suggestion click
   */
  onSuggestionClick(suggestion: Suggestion): void {
    if (this.disabled) return;
    
    this.suggestionSelected.emit(suggestion.text);
  }

  /**
   * Get category display info
   */
  getCategoryInfo(categoryId: string) {
    return this.categories.find(c => c.id === categoryId);
  }

  /**
   * Get suggestions count for category
   */
  getCategoryCount(categoryId: string): number {
    if (categoryId === 'all') {
      return this.suggestions.length;
    }
    return this.suggestions.filter(s => s.category === categoryId).length;
  }

  /**
   * Check if category is active
   */
  isCategoryActive(categoryId: string): boolean {
    return this.selectedCategory === categoryId;
  }

  /**
   * Get suggestion icon
   */
  getSuggestionIcon(suggestion: Suggestion): string {
    return suggestion.icon || this.getCategoryInfo(suggestion.category)?.icon || 'chat';
  }

  /**
   * Clear search
   */
  clearSearch(): void {
    this.searchTerm = '';
    this.filterSuggestions();
  }

  /**
   * Refresh suggestions
   */
  refreshSuggestions(): void {
    this.loadSuggestions();
    this.filterSuggestions();
  }

  /**
   * Get empty state message
   */
  getEmptyStateMessage(): string {
    if (this.searchTerm.trim()) {
      return `No suggestions found for "${this.searchTerm}"`;
    } else if (this.selectedCategory !== 'all') {
      const category = this.getCategoryInfo(this.selectedCategory);
      return `No ${category?.name.toLowerCase()} suggestions available`;
    } else {
      return 'No suggestions available';
    }
  }

  /**
   * Track by function for ngFor
   */
  trackBySuggestion(index: number, suggestion: Suggestion): string {
    return suggestion.id;
  }

  /**
   * Track by function for categories
   */
  trackByCategory(index: number, category: any): string {
    return category.id;
  }
}
