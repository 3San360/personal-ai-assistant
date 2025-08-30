import { Component, EventEmitter, Input, OnDestroy, OnInit, Output } from '@angular/core';
import { VoiceService } from '../../services/voice.service';
import { Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-voice-control',
  templateUrl: './voice-control.component.html',
  styleUrls: ['./voice-control.component.scss']
})
export class VoiceControlComponent implements OnInit, OnDestroy {
  @Input() disabled: boolean = false;
  @Output() voiceInput = new EventEmitter<string>();
  @Output() recordingStateChange = new EventEmitter<boolean>();

  isRecording: boolean = false;
  isProcessing: boolean = false;
  isSupported: boolean = false;
  audioLevel: number = 0;
  transcriptionText: string = '';
  errorMessage: string = '';
  
  private destroy$ = new Subject<void>();
  private animationFrameId: number | null = null;

  constructor(private voiceService: VoiceService) {}

  ngOnInit(): void {
    this.checkVoiceSupport();
    this.setupVoiceServiceSubscriptions();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.stopRecording();
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }

  /**
   * Check if voice recognition is supported
   */
  private checkVoiceSupport(): void {
    this.isSupported = this.voiceService.isSupported();
    if (!this.isSupported) {
      this.errorMessage = 'Voice recognition is not supported in this browser';
    }
  }

  /**
   * Setup voice service subscriptions
   */
  private setupVoiceServiceSubscriptions(): void {
    // Subscribe to recording state changes
    this.voiceService.isRecording$
      .pipe(takeUntil(this.destroy$))
      .subscribe(isRecording => {
        this.isRecording = isRecording;
        this.recordingStateChange.emit(isRecording);
        
        if (isRecording) {
          this.startAudioLevelAnimation();
        } else {
          this.stopAudioLevelAnimation();
        }
      });

    // Subscribe to processing state changes
    this.voiceService.isProcessing$
      .pipe(takeUntil(this.destroy$))
      .subscribe(isProcessing => {
        this.isProcessing = isProcessing;
      });

    // Subscribe to transcription results
    this.voiceService.transcriptionResult$
      .pipe(takeUntil(this.destroy$))
      .subscribe(result => {
        if (result.isFinal) {
          this.transcriptionText = result.text;
          this.voiceInput.emit(result.text);
          
          // Clear transcription after a delay
          setTimeout(() => {
            this.transcriptionText = '';
          }, 2000);
        } else {
          this.transcriptionText = result.text;
        }
      });

    // Subscribe to voice errors
    this.voiceService.error$
      .pipe(takeUntil(this.destroy$))
      .subscribe(error => {
        this.errorMessage = error;
        this.isRecording = false;
        this.isProcessing = false;
        
        // Clear error after a delay
        setTimeout(() => {
          this.errorMessage = '';
        }, 5000);
      });

    // Subscribe to audio level updates
    this.voiceService.audioLevel$
      .pipe(takeUntil(this.destroy$))
      .subscribe(level => {
        this.audioLevel = level;
      });
  }

  /**
   * Toggle voice recording
   */
  toggleRecording(): void {
    if (!this.isSupported || this.disabled) {
      return;
    }

    if (this.isRecording) {
      this.stopRecording();
    } else {
      this.startRecording();
    }
  }

  /**
   * Start voice recording
   */
  private startRecording(): void {
    this.errorMessage = '';
    this.voiceService.startRecording();
  }

  /**
   * Stop voice recording
   */
  private stopRecording(): void {
    this.voiceService.stopRecording();
  }

  /**
   * Start audio level animation
   */
  private startAudioLevelAnimation(): void {
    const animate = () => {
      if (this.isRecording) {
        this.animationFrameId = requestAnimationFrame(animate);
      }
    };
    animate();
  }

  /**
   * Stop audio level animation
   */
  private stopAudioLevelAnimation(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.audioLevel = 0;
  }

  /**
   * Get recording button icon
   */
  getRecordingIcon(): string {
    if (this.isProcessing) {
      return 'hourglass_empty';
    } else if (this.isRecording) {
      return 'stop';
    } else {
      return 'mic';
    }
  }

  /**
   * Get recording button tooltip
   */
  getRecordingTooltip(): string {
    if (!this.isSupported) {
      return 'Voice recognition not supported';
    } else if (this.disabled) {
      return 'Voice input disabled';
    } else if (this.isProcessing) {
      return 'Processing speech...';
    } else if (this.isRecording) {
      return 'Stop recording';
    } else {
      return 'Start voice recording';
    }
  }

  /**
   * Get recording button class
   */
  getRecordingButtonClass(): string {
    let baseClass = 'voice-button';
    
    if (this.isRecording) {
      baseClass += ' recording';
    }
    
    if (this.isProcessing) {
      baseClass += ' processing';
    }
    
    if (!this.isSupported || this.disabled) {
      baseClass += ' disabled';
    }
    
    return baseClass;
  }

  /**
   * Get audio level indicator style
   */
  getAudioLevelStyle(): any {
    const scale = 1 + (this.audioLevel * 0.3); // Scale between 1 and 1.3
    return {
      transform: `scale(${scale})`,
      opacity: this.audioLevel > 0.1 ? 1 : 0.6
    };
  }

  /**
   * Clear current error
   */
  clearError(): void {
    this.errorMessage = '';
  }

  /**
   * Handle keyboard shortcuts
   */
  onKeyDown(event: KeyboardEvent): void {
    // Space bar to toggle recording
    if (event.code === 'Space' && !event.repeat) {
      event.preventDefault();
      this.toggleRecording();
    }
    
    // Escape to stop recording
    if (event.code === 'Escape' && this.isRecording) {
      event.preventDefault();
      this.stopRecording();
    }
  }
}
