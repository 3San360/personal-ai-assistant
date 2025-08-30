import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';

import { ConfigService } from './services';
import { UserPreferences } from './models';

@Component({
  selector: 'app-root',
  template: `
    <div class="app-container" [class.dark-theme]="isDarkTheme">
      <!-- Header -->
      <mat-toolbar color="primary" class="app-header">
        <button 
          mat-icon-button 
          (click)="sidenav.toggle()"
          matTooltip="Toggle menu">
          <mat-icon>menu</mat-icon>
        </button>
        
        <span class="app-title">{{ appInfo.name }}</span>
        
        <span class="spacer"></span>
        
        <button 
          mat-icon-button 
          routerLink="/settings"
          matTooltip="Settings">
          <mat-icon>settings</mat-icon>
        </button>
      </mat-toolbar>

      <mat-sidenav-container class="app-sidenav-container">
        <!-- Side navigation -->
        <mat-sidenav 
          #sidenav 
          mode="over" 
          class="app-sidenav">
          <mat-nav-list>
            <a mat-list-item routerLink="/chat" (click)="sidenav.close()">
              <mat-icon matListIcon>chat</mat-icon>
              <span>Chat</span>
            </a>
            <a mat-list-item routerLink="/settings" (click)="sidenav.close()">
              <mat-icon matListIcon>settings</mat-icon>
              <span>Settings</span>
            </a>
            <mat-divider></mat-divider>
            <div mat-subheader>Features</div>
            <mat-list-item>
              <mat-icon matListIcon>wb_sunny</mat-icon>
              <span>Weather</span>
              <mat-icon 
                class="feature-status" 
                [class.enabled]="features.weatherIntegration">
                {{ features.weatherIntegration ? 'check_circle' : 'cancel' }}
              </mat-icon>
            </mat-list-item>
            <mat-list-item>
              <mat-icon matListIcon>article</mat-icon>
              <span>News</span>
              <mat-icon 
                class="feature-status" 
                [class.enabled]="features.newsIntegration">
                {{ features.newsIntegration ? 'check_circle' : 'cancel' }}
              </mat-icon>
            </mat-list-item>
            <mat-list-item>
              <mat-icon matListIcon>event</mat-icon>
              <span>Calendar</span>
              <mat-icon 
                class="feature-status" 
                [class.enabled]="features.calendarIntegration">
                {{ features.calendarIntegration ? 'check_circle' : 'cancel' }}
              </mat-icon>
            </mat-list-item>
            <mat-list-item>
              <mat-icon matListIcon>mic</mat-icon>
              <span>Voice Input</span>
              <mat-icon 
                class="feature-status" 
                [class.enabled]="features.voiceInput && config.voiceEnabled">
                {{ features.voiceInput && config.voiceEnabled ? 'check_circle' : 'cancel' }}
              </mat-icon>
            </mat-list-item>
          </mat-nav-list>
        </mat-sidenav>

        <!-- Main content -->
        <mat-sidenav-content class="app-content">
          <router-outlet></router-outlet>
        </mat-sidenav-content>
      </mat-sidenav-container>

      <!-- Footer -->
      <div class="app-footer">
        <span class="version">v{{ appInfo.version }}</span>
        <span class="spacer"></span>
        <span class="status" [class.online]="isOnline">
          {{ isOnline ? 'Online' : 'Offline' }}
        </span>
      </div>
    </div>
  `,
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {
  config: UserPreferences = {};
  appInfo = { name: 'Personal AI Assistant', version: '1.0.0' };
  features = {
    weatherIntegration: true,
    newsIntegration: true,
    calendarIntegration: true,
    voiceInput: true,
    voiceOutput: true
  };
  
  isOnline = navigator.onLine;
  isDarkTheme = false;
  
  private subscription = new Subscription();

  constructor(private configService: ConfigService) {}

  ngOnInit(): void {
    // Load app info and features from config service
    this.appInfo = this.configService.appInfo;
    this.features = this.configService.features;

    // Subscribe to configuration changes
    this.subscription.add(
      this.configService.config$.subscribe(config => {
        this.config = config;
        this.updateTheme();
      })
    );

    // Listen for online/offline status
    window.addEventListener('online', () => {
      this.isOnline = true;
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
    });
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }

  private updateTheme(): void {
    if (this.config.theme === 'dark') {
      this.isDarkTheme = true;
    } else if (this.config.theme === 'light') {
      this.isDarkTheme = false;
    } else {
      // Auto theme - check system preference
      this.isDarkTheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
  }
}
