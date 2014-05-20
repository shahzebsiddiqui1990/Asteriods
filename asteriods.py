"""
Author: Shahzeb Siddiqui
Date: 05/17/2014
Description: This is an implementation of Asteriods. The game contains a canvas where player maneuvers his/her ship to 
             dodge the rocks. The player can shoot missile from the ship using the [spacebar] button. The player starts
             out with 3 lives and every collision with rock, the player will lose a life. The player's score is the number
             of rocks destroyed.
             
Note: This code works with codeskulptor.org and will not work with tradition Python compiler because it uses library simplegui
      which is a custom made library
"""      
import simplegui
import math
import random

# globals for user interface
WIDTH = 800
HEIGHT = 600
score = 0
high_score = 0
lives = 3
time = 0.5
started = False
rock_group = set([])
missile_group = set([])
min_rock_ship_spawn_distance = 100

class ImageInfo:
    def __init__(self, center, size, radius = 0, lifespan = None, animated = False):
        self.center = center
        self.size = size
        self.radius = radius
        if lifespan:
            self.lifespan = lifespan
        else:
            self.lifespan = float('inf')
        self.animated = animated

    def get_center(self):
        return self.center

    def get_size(self):
        return self.size

    def get_radius(self):
        return self.radius

    def get_lifespan(self):
        return self.lifespan

    def get_animated(self):
        return self.animated

    
# art assets created by Kim Lathrop, may be freely re-used in non-commercial projects, please credit Kim
    
# debris images - debris1_brown.png, debris2_brown.png, debris3_brown.png, debris4_brown.png
#                 debris1_blue.png, debris2_blue.png, debris3_blue.png, debris4_blue.png, debris_blend.png
debris_info = ImageInfo([320, 240], [640, 480])
debris_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/debris2_blue.png")

# nebula images - nebula_brown.png, nebula_blue.png
nebula_info = ImageInfo([400, 300], [800, 600])
nebula_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/nebula_blue.s2014.png")

# splash image
splash_info = ImageInfo([200, 150], [400, 300])
splash_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/splash.png")

# ship image
ship_info = ImageInfo([45, 45], [90, 90], 35)
ship_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/double_ship.png")

# missile image - shot1.png, shot2.png, shot3.png
missile_info = ImageInfo([5,5], [10, 10], 3, 50)
missile_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/shot2.png")

# asteroid images - asteroid_blue.png, asteroid_brown.png, asteroid_blend.png
asteroid_info = ImageInfo([45, 45], [90, 90], 40)
asteroid_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/asteroid_blue.png")

# animated explosion - explosion_orange.png, explosion_blue.png, explosion_blue2.png, explosion_alpha.png
explosion_info = ImageInfo([64, 64], [128, 128], 17, 24, True)
explosion_image = simplegui.load_image("http://commondatastorage.googleapis.com/codeskulptor-assets/lathrop/explosion_alpha.png")

# sound assets purchased from sounddogs.com, please do not redistribute
soundtrack = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/soundtrack.mp3")
missile_sound = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/missile.mp3")
missile_sound.set_volume(.5)
ship_thrust_sound = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/thrust.mp3")
explosion_sound = simplegui.load_sound("http://commondatastorage.googleapis.com/codeskulptor-assets/sounddogs/explosion.mp3")

# helper functions to handle transformations
def angle_to_vector(ang):
    return [math.cos(ang), math.sin(ang)]

def dist(p,q):
    return math.sqrt((p[0] - q[0]) ** 2+(p[1] - q[1]) ** 2)


# Ship class
class Ship:
    def __init__(self, pos, vel, angle, image, info):
        self.pos = [pos[0],pos[1]]
        self.tip_pos = [pos[0]+45,pos[1]]
        self.vel = [vel[0],vel[1]]
        self.thrust = False
        self.angle = angle
        self.angle_vel = 0
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.accel_constant = 0.1
        self.friction_constant = 0.02
        
    def draw(self,canvas):
                
        canvas.draw_image(self.image,self.image_center,self.image_size,self.pos,self.image_size,self.angle)               

    def update(self):
        self.pos[0] = (self.pos[0] + self.vel[0]) % WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1]) % HEIGHT        
        
        self.angle += self.angle_vel
        self.forward_vector = angle_to_vector(self.angle)
        
        # friction update to velocity
        self.vel[0] *= (1 - self.friction_constant)
        self.vel[1] *= (1 - self.friction_constant)
        
        # velocity update with acceleration
        if self.thrust == True:
            
            self.vel[0] += self.accel_constant * self.forward_vector[0] 
            self.vel[1] += self.accel_constant * self.forward_vector[1] 
        
            
    def keydown_left(self):    
        self.angle_vel += -0.05
        
    def keydown_right(self):
        self.angle_vel += 0.05           
        
    def keyup_left(self):
        self.angle_vel = 0            
        
    def keyup_right(self):    
        self.angle_vel = 0
    
    def thruston(self):
        self.thrust = True
        self.image_center[0] += 90
        ship_thrust_sound.rewind()
        ship_thrust_sound.play()
    def thrustoff(self):    
       self.thrust = False
       self.image_center[0] += -90
       ship_thrust_sound.pause()
        
    def shoot(self):
        global a_missile
        
        missile_vel = [self.vel[0] + self.forward_vector[0] * 4,self.vel[1] + self.forward_vector[1] * 4]        
        # missile position calculated by finding tip of ship, it uses forward vector to find tip
        missile_pos = [self.pos[0]+45*self.forward_vector[0],self.pos[1]+45*self.forward_vector[1]] 
        
        a_missile = Sprite(missile_pos, missile_vel, self.angle, 0, missile_image, missile_info, missile_sound)
        missile_group.add(a_missile)
        
# Sprite class
class Sprite:
    def __init__(self, pos, vel, ang, ang_vel, image, info, sound = None):
        self.pos = [pos[0],pos[1]]
        self.vel = [vel[0],vel[1]]
        self.angle = ang
        self.angle_vel = ang_vel
        self.image = image
        self.image_center = info.get_center()
        self.image_size = info.get_size()
        self.radius = info.get_radius()
        self.lifespan = info.get_lifespan()
        self.animated = info.get_animated()
        self.age = 0
        if sound:
            sound.rewind()
            sound.play()
   
    def draw(self, canvas):        
        canvas.draw_image(self.image,self.image_center,self.image_size,self.pos,self.image_size,self.angle)
    
    def update(self):
        self.pos[0] = (self.pos[0] + self.vel[0]) % WIDTH
        self.pos[1] = (self.pos[1] + self.vel[1]) % HEIGHT
        
        self.angle += self.angle_vel
        
        self.age+= 1
        
        if self.age >= self.lifespan:
            return True
        else:
            return False
    
    def collide(self,other_object):
        distance_between_object_pos = dist(self.pos,other_object.pos)
        
        if distance_between_object_pos < (self.radius + other_object.radius):
            return True
        else:
            return False
                
           
def draw(canvas):
    global time, started, lives, score, prev_score, high_score
    
    # animiate background
    time += 1
    wtime = (time / 4) % WIDTH
    center = debris_info.get_center()
    size = debris_info.get_size()
    canvas.draw_image(nebula_image, nebula_info.get_center(), nebula_info.get_size(), [WIDTH / 2, HEIGHT / 2], [WIDTH, HEIGHT])
    canvas.draw_image(debris_image, center, size, (wtime - WIDTH / 2, HEIGHT / 2), (WIDTH, HEIGHT))
    canvas.draw_image(debris_image, center, size, (wtime + WIDTH / 2, HEIGHT / 2), (WIDTH, HEIGHT))
    
    #draw lives and score field    
    canvas.draw_text("Lives: " + str(lives), [50,50], 24,'Red')
    canvas.draw_text("Score: " + str(score), [650,50], 24,'Red')
    if (not started):                
        canvas.draw_text("High Score: " + str(high_score), [600,100], 24, 'Blue')
    # draw ship 
    my_ship.draw(canvas)
    
    # update ship 
    my_ship.update()
    
    num_collide = 0
    num_missile_rock_collide = 0
    process_sprite_group(rock_group,canvas)
    process_sprite_group(missile_group,canvas)
    
    num_missile_rock_collide = group_group_collide(rock_group,missile_group)
    score += num_missile_rock_collide
    num_collide = group_collide(rock_group,my_ship)    
    lives = lives - num_collide
    
    if lives <= 0:
        started = False
        for rock in list(rock_group):
            rock_group.remove(rock)            
            if score > high_score:
                high_score = score            
            soundtrack.rewind()
            soundtrack.play()
            lives = 3            
    
    # draw splash screen if not started
    if not started:
        canvas.draw_image(splash_image, splash_info.get_center(), 
                          splash_info.get_size(), [WIDTH / 2, HEIGHT / 2], 
                          splash_info.get_size())
            
# timer handler that spawns a rock    
def rock_spawner():
    global rock_group, started
    if started == False:
        return
    
    rock_pos = [random.randrange(0, WIDTH), random.randrange(0, HEIGHT)]
    rock_vel = [random.random() * .6 - .3, random.random() * .6 - .3]
    rock_avel = random.random() * .2 - .1    
    
    if len(rock_group) < 20:      
       a_rock = Sprite(rock_pos, rock_vel, 0, rock_avel, asteroid_image, asteroid_info)     
       if dist(rock_pos,my_ship.pos) >= min_rock_ship_spawn_distance:                
            rock_group.add(a_rock)
    
def process_sprite_group(sprite_set,canvas):
    for sprite in list(sprite_set):
        if sprite.update() == True:
            sprite_set.remove(sprite)
        else:    
            sprite.draw(canvas)

def group_collide(group,other_object):
    number_collisions = 0    
    for sprite in list(group):
        if sprite.collide(other_object) == True:
            group.remove(sprite)
            number_collisions += 1
    return number_collisions

def group_group_collide(rockgroup,missilegroup):
    total_collisions_between_missile_rock = 0
    for rock in list(rockgroup):
        ret_val = 0
        ret_val = group_collide(missilegroup,rock) 
        if ret_val > 0:
            rockgroup.remove(rock)
        total_collisions_between_missile_rock += ret_val
    
    
    return total_collisions_between_missile_rock
def keydown(key):
    if key == simplegui.KEY_MAP['left']:
        my_ship.keydown_left()
    elif key == simplegui.KEY_MAP['right']:    
        my_ship.keydown_right()
    elif key == simplegui.KEY_MAP['up']:        
        my_ship.thruston()
    elif key == simplegui.KEY_MAP['space']:
        my_ship.shoot()
def keyup(key):
    if key == simplegui.KEY_MAP['left']:
        my_ship.keyup_left()
    elif key == simplegui.KEY_MAP['right']:
        my_ship.keyup_right()
    elif key == simplegui.KEY_MAP['up']:           
        my_ship.thrustoff()

def click(pos):        
    global started, score
    center = [WIDTH / 2, HEIGHT / 2]
    size = splash_info.get_size()
    inwidth = (center[0] - size[0] / 2) < pos[0] < (center[0] + size[0] / 2)
    inheight = (center[1] - size[1] / 2) < pos[1] < (center[1] + size[1] / 2)
    if (not started) and inwidth and inheight:
        started = True
        score = 0
        soundtrack.pause()
        
# initialize frame
frame = simplegui.create_frame("Asteroids", WIDTH, HEIGHT)

# initialize ship and two sprites
my_ship = Ship([WIDTH / 2, HEIGHT / 2], [0, 0], 0, ship_image, ship_info)

# register handlers
frame.set_draw_handler(draw)
frame.set_keydown_handler(keydown)
frame.set_keyup_handler(keyup)
frame.set_mouseclick_handler(click)
timer = simplegui.create_timer(1000.0, rock_spawner)

# get things rolling
timer.start()
frame.start()

