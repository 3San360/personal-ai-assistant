import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ConfigService } from '../../services/config.service';
import { Subject, takeUntil } from 'rxjs';

export interface SettingsData {
  theme: 'light' | 'dark' | 'auto';
  voiceEnabled: boolean;
  voiceSpeed: number;
  voicePitch: number;
  autoSend: boolean;
  showTimestamps: boolean;
  maxContextMessages: number;
  apiTimeout: number;
  language: string;
  notifications: boolean;
  soundEffects: boolean;
}

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.scss']
})
export class SettingsComponent implements OnInit, OnDestroy {
  settingsForm: FormGroup;
  isLoading: boolean = false;
  availableLanguages = [
    { code: 'en-US', name: 'English (US)' },
    { code: 'en-GB', name: 'English (UK)' },
    { code: 'es-ES', name: 'Spanish' },
    { code: 'fr-FR', name: 'French' },
    { code: 'de-DE', name: 'German' },
    { code: 'it-IT', name: 'Italian' },
    { code: 'pt-BR', name: 'Portuguese (Brazil)' },
    { code: 'ja-JP', name: 'Japanese' },
    { code: 'ko-KR', name: 'Korean' },
    { code: 'zh-CN', name: 'Chinese (Simplified)' }
  ];

  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private configService: ConfigService,
    private snackBar: MatSnackBar
  ) {
    this.settingsForm = this.createForm();
  }

  ngOnInit(): void {
    this.loadSettings();
    this.setupFormSubscriptions();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Create the settings form
   */
  private createForm(): FormGroup {
    return this.fb.group({
      theme: ['light', Validators.required],
      voiceEnabled: [true],
      voiceSpeed: [1, [Validators.min(0.1), Validators.max(3)]],
      voicePitch: [1, [Validators.min(0), Validators.max(2)]],
      autoSend: [false],
      showTimestamps: [true],
      maxContextMessages: [10, [Validators.min(1), Validators.max(50)]],
      apiTimeout: [30, [Validators.min(5), Validators.max(120)]],
      language: ['en-US', Validators.required],
      notifications: [true],
      soundEffects: [true]
    });
  }

  /**
   * Load current settings
   */
  private loadSettings(): void {
    this.isLoading = true;
    
    this.configService.getSettings()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (settings) => {
          this.settingsForm.patchValue(settings);
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Failed to load settings:', error);
          this.showErrorMessage('Failed to load settings');
          this.isLoading = false;
        }
      });
  }

  /**
   * Setup form change subscriptions
   */
  private setupFormSubscriptions(): void {
    // Auto-save theme changes
    this.settingsForm.get('theme')?.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(theme => {
        this.configService.updateTheme(theme);
      });

    // Validate voice settings
    this.settingsForm.get('voiceSpeed')?.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(speed => {
        if (speed && (speed < 0.1 || speed > 3)) {
          this.settingsForm.get('voiceSpeed')?.setErrors({ range: true });
        }
      });

    this.settingsForm.get('voicePitch')?.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(pitch => {
        if (pitch && (pitch < 0 || pitch > 2)) {
          this.settingsForm.get('voicePitch')?.setErrors({ range: true });
        }
      });
  }

  /**
   * Save settings
   */
  saveSettings(): void {
    if (this.settingsForm.invalid) {
      this.markFormGroupTouched();
      this.showErrorMessage('Please fix the errors in the form');
      return;
    }

    this.isLoading = true;
    const settings: SettingsData = this.settingsForm.value;

    this.configService.saveSettings(settings)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isLoading = false;
          this.showSuccessMessage('Settings saved successfully');
        },
        error: (error) => {
          console.error('Failed to save settings:', error);
          this.isLoading = false;
          this.showErrorMessage('Failed to save settings');
        }
      });
  }

  /**
   * Reset settings to defaults
   */
  resetToDefaults(): void {
    const defaultSettings: SettingsData = {
      theme: 'light',
      voiceEnabled: true,
      voiceSpeed: 1,
      voicePitch: 1,
      autoSend: false,
      showTimestamps: true,
      maxContextMessages: 10,
      apiTimeout: 30,
      language: 'en-US',
      notifications: true,
      soundEffects: true
    };

    this.settingsForm.patchValue(defaultSettings);
    this.showInfoMessage('Settings reset to defaults');
  }

  /**
   * Test voice settings
   */
  testVoice(): void {
    const settings = this.settingsForm.value;
    const testText = 'This is a test of the voice settings.';
    
    // This would typically call the voice service to test the current settings
    this.configService.testVoiceSettings(testText, {
      speed: settings.voiceSpeed,
      pitch: settings.voicePitch,
      language: settings.language
    }).subscribe({
      next: () => {
        this.showSuccessMessage('Voice test completed');
      },
      error: (error) => {
        console.error('Voice test failed:', error);
        this.showErrorMessage('Voice test failed');
      }
    });
  }

  /**
   * Export settings
   */
  exportSettings(): void {
    const settings = this.settingsForm.value;
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'ai-assistant-settings.json';
    link.click();
    
    this.showSuccessMessage('Settings exported successfully');
  }

  /**
   * Import settings
   */
  importSettings(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const settings = JSON.parse(e.target?.result as string);
        this.settingsForm.patchValue(settings);
        this.showSuccessMessage('Settings imported successfully');
      } catch (error) {
        console.error('Failed to import settings:', error);
        this.showErrorMessage('Invalid settings file');
      }
    };
    reader.readAsText(file);
    
    // Reset input value to allow re-importing the same file
    input.value = '';
  }

  /**
   * Get theme display name
   */
  getThemeDisplayName(theme: string): string {
    switch (theme) {
      case 'light': return 'Light';
      case 'dark': return 'Dark';
      case 'auto': return 'Auto (System)';
      default: return theme;
    }
  }

  /**
   * Get field error message
   */
  getFieldError(fieldName: string): string {
    const field = this.settingsForm.get(fieldName);
    if (!field || !field.errors || !field.touched) return '';

    const errors = field.errors;
    
    if (errors['required']) return `${fieldName} is required`;
    if (errors['min']) return `Minimum value is ${errors['min'].min}`;
    if (errors['max']) return `Maximum value is ${errors['max'].max}`;
    if (errors['range']) return `Value must be within valid range`;
    
    return 'Invalid value';
  }

  /**
   * Check if field has error
   */
  hasFieldError(fieldName: string): boolean {
    const field = this.settingsForm.get(fieldName);
    return !!(field && field.errors && field.touched);
  }

  /**
   * Mark all form fields as touched
   */
  private markFormGroupTouched(): void {
    Object.keys(this.settingsForm.controls).forEach(key => {
      const control = this.settingsForm.get(key);
      control?.markAsTouched();
    });
  }

  /**
   * Show success message
   */
  private showSuccessMessage(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  /**
   * Show error message
   */
  private showErrorMessage(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  /**
   * Show info message
   */
  private showInfoMessage(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 3000,
      panelClass: ['info-snackbar']
    });
  }
}
