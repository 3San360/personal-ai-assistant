import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { UserPreferences } from '@app/models';
import { environment } from '@environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ConfigService {
  private readonly STORAGE_KEY = 'personalAssistantConfig';

  // Default configuration
  private defaultConfig: UserPreferences = {
    location: '',
    units: 'metric',
    language: 'en-US',
    voiceEnabled: true,
    notifications: true,
    theme: 'auto'
  };

  // Current configuration state
  private configSubject = new BehaviorSubject<UserPreferences>(this.defaultConfig);
  public config$ = this.configSubject.asObservable();

  constructor() {
    this.loadConfiguration();
  }

  /**
   * Load configuration from localStorage
   */
  private loadConfiguration(): void {
    try {
      const savedConfig = localStorage.getItem(this.STORAGE_KEY);
      if (savedConfig) {
        const parsedConfig = JSON.parse(savedConfig);
        const mergedConfig = { ...this.defaultConfig, ...parsedConfig };
        this.configSubject.next(mergedConfig);
      }
    } catch (error) {
      console.error('Error loading configuration:', error);
      this.configSubject.next(this.defaultConfig);
    }
  }

  /**
   * Save configuration to localStorage
   */
  private saveConfiguration(config: UserPreferences): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(config));
    } catch (error) {
      console.error('Error saving configuration:', error);
    }
  }

  /**
   * Update configuration
   */
  updateConfig(updates: Partial<UserPreferences>): void {
    const currentConfig = this.configSubject.value;
    const newConfig = { ...currentConfig, ...updates };
    
    this.configSubject.next(newConfig);
    this.saveConfiguration(newConfig);
  }

  /**
   * Reset configuration to defaults
   */
  resetConfig(): void {
    this.configSubject.next(this.defaultConfig);
    this.saveConfiguration(this.defaultConfig);
  }

  /**
   * Get current configuration
   */
  get currentConfig(): UserPreferences {
    return this.configSubject.value;
  }

  /**
   * Get application environment
   */
  get environment() {
    return environment;
  }

  /**
   * Get API URL
   */
  get apiUrl(): string {
    return environment.apiUrl;
  }

  /**
   * Get app information
   */
  get appInfo() {
    return {
      name: environment.appName,
      version: environment.version,
      production: environment.production
    };
  }

  /**
   * Get feature flags
   */
  get features() {
    return environment.features;
  }

  /**
   * Check if a feature is enabled
   */
  isFeatureEnabled(feature: keyof typeof environment.features): boolean {
    return environment.features[feature] || false;
  }

  /**
   * Get voice settings
   */
  get voiceSettings() {
    return environment.voice;
  }

  /**
   * Get chat settings
   */
  get chatSettings() {
    return environment.chat;
  }

  /**
   * Get UI settings
   */
  get uiSettings() {
    return environment.ui;
  }
}
