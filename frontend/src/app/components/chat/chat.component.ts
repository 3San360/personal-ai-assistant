import { Component, OnInit, OnDestroy, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subscription, combineLatest } from 'rxjs';

import { ChatService, VoiceService, ConfigService } from '@app/services';
import { ChatMessage, UserPreferences, VoiceState } from '@app/models';

@Component({
  selector: 'app-chat',
  template: `
    <div class="chat-container">
      <!-- Chat messages area -->
      <div class="messages-container" #messagesContainer>
        <div class="messages-wrapper">
          <!-- Welcome message -->
          <div class="welcome-message" *ngIf="messages.length === 0">
            <mat-card class="welcome-card">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>smart_toy</mat-icon>
                  Welcome to Personal AI Assistant
                </mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <p>I can help you with:</p>
                <ul>
                  <li><mat-icon>wb_sunny</mat-icon> Weather information</li>
                  <li><mat-icon>article</mat-icon> Latest news</li>
                  <li><mat-icon>event</mat-icon> Calendar events</li>
                  <li><mat-icon>mic</mat-icon> Voice commands</li>
                </ul>
                <p>Try asking me something or click on the suggestions below!</p>
              </mat-card-content>
            </mat-card>
          </div>

          <!-- Chat messages -->
          <div class="messages-list">
            <app-message 
              *ngFor="let message of messages; trackBy: trackByMessageId"
              [message]="message"
              [showTimestamp]="showTimestamps">
            </app-message>
          </div>

          <!-- Typing indicator -->
          <div class="typing-indicator" *ngIf="isTyping">
            <mat-card class="typing-card">
              <div class="typing-content">
                <mat-icon>smart_toy</mat-icon>
                <span>Assistant is typing</span>
                <div class="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </mat-card>
          </div>
        </div>
      </div>

      <!-- Suggestions -->
      <app-suggestions 
        *ngIf="showSuggestions"
        (suggestionSelected)="onSuggestionSelected($event)">
      </app-suggestions>

      <!-- Input area -->
      <div class="input-container">
        <mat-card class="input-card">
          <div class="input-wrapper">
            <!-- Voice control -->
            <app-voice-control
              [conversationId]="currentConversationId"
              (voiceResult)="onVoiceResult($event)"
              (voiceError)="onVoiceError($event)">
            </app-voice-control>

            <!-- Text input -->
            <mat-form-field class="message-input" appearance="outline">
              <mat-label>Type your message...</mat-label>
              <input 
                matInput 
                [formControl]="messageControl"
                [maxlength]="maxMessageLength"
                (keyup.enter)="sendMessage()"
                [disabled]="isLoading"
                placeholder="Ask me about weather, news, calendar, or anything else!">
              <mat-hint align="end">
                {{ messageControl.value?.length || 0 }} / {{ maxMessageLength }}
              </mat-hint>
            </mat-form-field>

            <!-- Send button -->
            <button 
              mat-fab 
              color="primary"
              [disabled]="!messageControl.valid || isLoading"
              (click)="sendMessage()"
              matTooltip="Send message"
              class="send-button">
              <mat-icon *ngIf="!isLoading">send</mat-icon>
              <mat-spinner 
                *ngIf="isLoading" 
                diameter="24" 
                color="accent">
              </mat-spinner>
            </button>
          </div>

          <!-- Quick actions -->
          <div class="quick-actions" *ngIf="!isLoading">
            <button 
              mat-button 
              color="primary"
              (click)="sendQuickMessage('What\\'s the weather like?')"
              matTooltip="Get weather">
              <mat-icon>wb_sunny</mat-icon>
              Weather
            </button>
            <button 
              mat-button 
              color="primary"
              (click)="sendQuickMessage('Show me the latest news')"
              matTooltip="Get news">
              <mat-icon>article</mat-icon>
              News
            </button>
            <button 
              mat-button 
              color="primary"
              (click)="sendQuickMessage('What\\'s on my calendar today?')"
              matTooltip="View calendar">
              <mat-icon>event</mat-icon>
              Calendar
            </button>
            <button 
              mat-button 
              color="primary"
              (click)="sendQuickMessage('Help - what can you do?')"
              matTooltip="Get help">
              <mat-icon>help</mat-icon>
              Help
            </button>
          </div>
        </mat-card>
      </div>
    </div>
  `,
  styleUrls: ['./chat.component.scss']
})
export class ChatComponent implements OnInit, OnDestroy, AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;

  messages: ChatMessage[] = [];
  messageControl = new FormControl('', [
    Validators.required,
    Validators.maxLength(1000)
  ]);
  
  isLoading = false;
  isTyping = false;
  showSuggestions = true;
  showTimestamps = true;
  maxMessageLength = 1000;
  
  currentConversationId: string | null = null;
  userPreferences: UserPreferences = {};
  voiceState: VoiceState = {
    isRecording: false,
    isProcessing: false,
    isSupported: false
  };

  private subscription = new Subscription();
  private shouldScrollToBottom = false;

  constructor(
    private chatService: ChatService,
    private voiceService: VoiceService,
    private configService: ConfigService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadConfiguration();
    this.subscribeToChatState();
    this.subscribeToVoiceState();
    this.initializeConversation();
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScrollToBottom) {
      this.scrollToBottom();
      this.shouldScrollToBottom = false;
    }
  }

  /**
   * Load configuration and preferences
   */
  private loadConfiguration(): void {
    this.subscription.add(
      this.configService.config$.subscribe(config => {
        this.userPreferences = config;
        this.showTimestamps = this.configService.uiSettings.showTimestamps;
        this.maxMessageLength = this.configService.chatSettings.maxMessageLength;
      })
    );
  }

  /**
   * Subscribe to chat service state
   */
  private subscribeToChatState(): void {
    // Subscribe to messages
    this.subscription.add(
      this.chatService.messages$.subscribe(messages => {
        this.messages = messages;
        this.showSuggestions = messages.length === 0;
        this.shouldScrollToBottom = true;
      })
    );

    // Subscribe to typing indicator
    this.subscription.add(
      this.chatService.isTyping$.subscribe(isTyping => {
        this.isTyping = isTyping;
        if (isTyping) {
          this.shouldScrollToBottom = true;
        }
      })
    );

    // Subscribe to current conversation
    this.subscription.add(
      this.chatService.currentConversation$.subscribe(conversation => {
        this.currentConversationId = conversation?.id || null;
      })
    );
  }

  /**
   * Subscribe to voice service state
   */
  private subscribeToVoiceState(): void {
    this.subscription.add(
      this.voiceService.voiceState$.subscribe(state => {
        this.voiceState = state;
      })
    );
  }

  /**
   * Initialize conversation
   */
  private initializeConversation(): void {
    if (!this.currentConversationId) {
      this.chatService.createConversation(this.userPreferences).subscribe({
        next: (response) => {
          if (response.success) {
            console.log('New conversation created:', response.data?.conversation_id);
          }
        },
        error: (error) => {
          console.error('Failed to create conversation:', error);
          this.showError('Failed to initialize conversation');
        }
      });
    }
  }

  /**
   * Send a text message
   */
  sendMessage(): void {
    if (!this.messageControl.valid || this.isLoading) {
      return;
    }

    const message = this.messageControl.value?.trim();
    if (!message) {
      return;
    }

    this.isLoading = true;
    this.messageControl.setValue('');

    this.chatService.sendMessage(
      message,
      this.currentConversationId || undefined,
      this.userPreferences
    ).subscribe({
      next: (response) => {
        this.isLoading = false;
        
        if (response.success && response.data) {
          // Handle voice output if enabled
          if (this.userPreferences.voiceEnabled && this.voiceState.isSupported) {
            this.speakResponse(response.data.message);
          }
        } else {
          this.showError(response.error || 'Failed to send message');
        }
      },
      error: (error) => {
        this.isLoading = false;
        console.error('Chat error:', error);
        this.showError('Failed to send message. Please try again.');
      }
    });
  }

  /**
   * Send a quick message
   */
  sendQuickMessage(message: string): void {
    this.messageControl.setValue(message);
    this.sendMessage();
  }

  /**
   * Handle suggestion selection
   */
  onSuggestionSelected(suggestion: string): void {
    this.messageControl.setValue(suggestion);
    this.sendMessage();
  }

  /**
   * Handle voice recognition result
   */
  onVoiceResult(result: { text: string; confidence: number }): void {
    this.messageControl.setValue(result.text);
    
    // Auto-send if confidence is high
    if (result.confidence > 0.8) {
      this.sendMessage();
    } else {
      this.showInfo(`Voice recognized: "${result.text}" (Confidence: ${(result.confidence * 100).toFixed(0)}%)`);
    }
  }

  /**
   * Handle voice recognition error
   */
  onVoiceError(error: string): void {
    this.showError(`Voice recognition error: ${error}`);
  }

  /**
   * Speak response using text-to-speech
   */
  private speakResponse(text: string): void {
    if (this.voiceService.isSupported) {
      this.voiceService.speakText(text).subscribe({
        next: () => {
          console.log('Speech synthesis completed');
        },
        error: (error) => {
          console.error('Speech synthesis error:', error);
        }
      });
    }
  }

  /**
   * Scroll to bottom of messages
   */
  private scrollToBottom(): void {
    try {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    } catch (error) {
      console.error('Error scrolling to bottom:', error);
    }
  }

  /**
   * Track function for message list
   */
  trackByMessageId(index: number, message: ChatMessage): string {
    return message.id;
  }

  /**
   * Show error message
   */
  private showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  /**
   * Show info message
   */
  private showInfo(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 3000,
      panelClass: ['info-snackbar']
    });
  }

  /**
   * Clear conversation
   */
  clearConversation(): void {
    this.chatService.clearConversation();
    this.initializeConversation();
  }
}
