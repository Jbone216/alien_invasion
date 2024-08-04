import sys 
from time import sleep

import pygame

from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien


class AlienInvasion:
    """Class to manage the game assets and behavior"""

    def __init__(self):
        """Initialize the game and create game resources."""
        pygame.init()
        self.clock = pygame.time.Clock()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((1200,800))
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        #Create an instance to store the game stats, and create scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        #set background color
        self.bg_color = (230, 230, 230)

        #Start Aiien Invasion in an active state
        self.game_active = False
        
        #Make the PLAY button
        self.play_button = Button(self, "Play")

    def run_game(self):
        """Start the main loop for the game"""
        while True:
            self._check_events()

            if self.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            

                ##Rid of bullets tht have disappeared
                for bullet in self.bullets.copy():
                    if bullet.rect.bottom <0:
                        self.bullets.remove(bullet)
                print(len(self.bullets))

            self._update_screen()
            self.clock.tick(60)
            
    def _check_events(self):
        """Respond to key press and mouse events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
    
    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            #reset the game settings
            self.settings.initialize_dynamic_settings()
            #reset game stats
            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()
            self.game_active = True

            #Get rid of remaining bullets/aliens
            self.bullets.empty()
            self.aliens.empty()

            #Create a new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()

            #hide the mouse cursor
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self,event):
        """respond to key presses"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_SPACE:
            self._fire_bullet() 
        elif event.key == pygame.K_q:
            sys.exit()
         

    def _check_keyup_events(self,event):
        """Respond to key releases""" 
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False           
                
    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group"""
        if len(self.bullets) < self.settings.bullets_allowed: #####
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)    
                
    def _update_bullets(self):
        """Update position of bullets and get rid of old ones"""
        self.bullets.update()
        
        #get rid of bullets off screen
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """respond to bullet alien collisions"""
        #remove any bullets and aliens that have collided
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)
        
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points *len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()
        
        if not self.aliens:
            #destroy existing bullets and create new fleet
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            #increase level
            self.stats.level += 1
            self.sb.prep_level()


    def _update_aliens(self):
        """Check if the fleet is at an edge, then update the postion"""
        self._check_fleet_edges()
        self.aliens.update()

        #look for alien ship collisions 
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        #look for aliens hitting the bottom of the screen
        self._check_aliens_bottom()
                    
    def _create_fleet(self):
        """create the fleet of aliens"""
        #creat an alien and keep adding aliens until there's no room left
        #spacing between each one is 1 alien width and 1 alien height
        #make an alien
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width

                #Finished a row, reset x value and increment y value
            current_x = alien_width
            current_y += 2 *alien_height

    def _create_alien(self, x_position, y_position):
            """create an alien and place it in the fleet"""
            new_alien = Alien(self)
            new_alien.x = x_position
            new_alien.rect.x = x_position
            new_alien.rect.y = y_position
            self.aliens.add(new_alien)
    
    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and chenge the fleets direction"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *=-1
            

    def _update_screen(self):
            """Update images on the screen and flip to new screen"""
            self.screen.fill(self.settings.bg_color)
            for bullet in self.bullets.sprites():
                bullet.draw_bullet()
            self.ship.blitme()
            self.aliens.draw(self.screen)

            #Draw the score information
            self.sb.show_score()

            #Draw the play button if the game is inactive
            if not  self.game_active:
                self.play_button.draw_button()

            #Make the most recently drawn scren visible
            pygame.display.flip()
            self.clock.tick(60) ###might be issue

    def _ship_hit(self):
        """respond to the ship being hit by an alien"""
        if self.stats.ships_left > 0:
            #decrement ships left and update scoreboard
            self.stats.ships_left -=1
            self.sb.prep_ships()

            #Get rid of remaining bullets and aliens
            self.bullets.empty()
            self.aliens.empty()

            #create new fleet and center the ship
            self._create_fleet()
            self.ship.center_ship()
        
            #pause
            sleep(.5)

        else: 
            self.game_active = False
            pygame.mouse.set_visible = (True)

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen"""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                #treat the same as if ship got hit
                self._ship_hit()
                break
        

if __name__ == '__main__':
    #make game instane, and run the game
    ai = AlienInvasion()
    ai.run_game()

