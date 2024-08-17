import pygame
import random
import numpy as np

# Initialiser pygame
pygame.init()

# Créer l'écran
screen = pygame.display.set_mode((1280, 720))
# Titre et icône
pygame.display.set_caption("Space Invaders (AI Version)")

# Couleurs
over_text_color = (255, 215, 0)
wall_color = (255, 10, 50)  # couleur pour les murs

# Charger les images
player_img = pygame.image.load('player.png')
enemy_img = pygame.image.load('enemy.png')
bullet_img = pygame.image.load('bullet.png')
enemy_bullet_img = pygame.image.load('enemy_bullet.png')

# Redimensionner les images
player_img = pygame.transform.scale(player_img, (50, 50))
enemy_img = pygame.transform.scale(enemy_img, (50, 50))
bullet_img = pygame.transform.scale(bullet_img, (10, 20))
enemy_bullet_img = pygame.transform.scale(enemy_bullet_img, (10, 20))

# Joueur
playerX = 640
playerY = 650
playerX_change = 0

lives = 3  # Le joueur commence avec 3 vies

# Murs
walls = [
    {"rect": pygame.Rect(100, 600, 70, 30), "health": 5},
    {"rect": pygame.Rect(300, 600, 70, 30), "health": 5},
    {"rect": pygame.Rect(500, 600, 70, 30), "health": 5},
    {"rect": pygame.Rect(700, 600, 70, 30), "health": 5},
    {"rect": pygame.Rect(900, 600, 70, 30), "health": 5},
    {"rect": pygame.Rect(1100, 600, 70, 30), "health": 5}
]

# Ennemi
enemyX = []
enemyY = []
enemyX_change = []
enemyY_change = []
num_of_enemies = 36  # Grille 6x6

# Paramètres du Q-Learning
alpha = 0.7  # Taux d'apprentissage
gamma = 0.9  # Facteur de réduction
epsilon = 0.07  # Facteur d'exploration

# Définir l'espace des états et des actions
num_states = 128  # C'est un exemple; ajustez en fonction de votre espace d'état réel
num_actions = 2   # 0 : Ne pas tirer, 1 : Tirer

# Initialiser la table Q
q_table = np.zeros((num_states, num_actions))

def spawn_enemy_grid():
    global enemyX, enemyY, enemyX_change, enemyY_change
    enemyX = []
    enemyY = []
    enemyX_change = []
    enemyY_change = []
    rows = 6
    columns = 6
    padding_x = 80
    padding_y = 60
    start_x = 420
    start_y = 50

    for i in range(rows):
        for j in range(columns):
            x = start_x + j * padding_x
            y = start_y + i * padding_y
            enemyX.append(x)
            enemyY.append(y)
            enemyX_change.append(0.3)
            enemyY_change.append(40)

# Remplir les ennemis dans une formation en grille
spawn_enemy_grid()

# Balle du joueur
bulletX = 0
bulletY = 650
bulletX_change = 0
bulletY_change = 7
bullet_state = "ready"

# Balles des ennemis
enemy_bullets = []

# Score
score_value = 0
font = pygame.font.Font('freesansbold.ttf', 32)
textX = 10
textY = 10

# Texte de fin de jeu
over_font = pygame.font.Font('freesansbold.ttf', 64)

def show_score(x, y):
    score = font.render("Score : " + str(score_value), True, over_text_color)
    screen.blit(score, (x, y))
    
def show_lives(x, y):
    lives_text = font.render("Lives : " + str(lives), True, over_text_color)
    screen.blit(lives_text, (x, y))

def game_over_text():
    over_text = over_font.render("GAME OVER", True, over_text_color)
    text_rect = over_text.get_rect(center=(1280 // 2, 720 // 2 - 20))
    screen.blit(over_text, text_rect)
    # Positionner le score juste en dessous de "GAME OVER"
    score_text = font.render("Score : " + str(score_value), True, over_text_color)
    score_rect = score_text.get_rect(center=(1280 // 2, 720 // 2 + 40))
    screen.blit(score_text, score_rect)

def player(x, y):
    screen.blit(player_img, (x, y))

def enemy(x, y):
    screen.blit(enemy_img, (x, y))

def fire_bullet(x, y):
    screen.blit(bullet_img, (x + 20, y + 10))

def fire_enemy_bullet(x, y):
    enemy_bullets.append([x + 20, y + 10])

def is_collision(entityX, entityY, bulletX, bulletY):
    # Dimensions du sprite de l'ennemi et du missile
    enemy_width = 50
    enemy_height = 50
    bullet_width = 10
    bullet_height = 20

    # Vérifier les collisions
    if (bulletX > entityX and bulletX < entityX + enemy_width) and (bulletY > entityY and bulletY < entityY + enemy_height):
        return True
    return False

def wall_collision(wall_rect, bulletX, bulletY):
    return wall_rect.collidepoint(bulletX, bulletY)

def draw_walls():
    for wall in walls:
        pygame.draw.rect(screen, wall_color, wall["rect"])
        
def get_state(enemyX, playerX):
    # L'état est déterminé par la position relative de l'ennemi par rapport au joueur
    return int((enemyX - playerX) // 100) + 4  # Exemple de calcul simple d'état

def choose_action(state):
    if np.random.uniform(0, 1) < epsilon:
        return np.random.choice(num_actions)  # Exploration
    else:
        return np.argmax(q_table[state, :])  # Exploitation

def update_q_table(state, action, reward, next_state):
    predict = q_table[state, action]
    target = reward + gamma * np.max(q_table[next_state, :])
    q_table[state, action] = (1 - alpha) * predict + alpha * target

def get_reward(shot, hit):
    if hit:
        return 100  # Récompense pour avoir touché le joueur
    elif shot:
        return -10  # Pénalité pour avoir tiré et manqué
    else:
        return 0  # Aucune action entreprise

# Horloge pour contrôler le taux de rafraîchissement
clock = pygame.time.Clock()

# Charger l'image de fond
background_img = pygame.image.load('bg.jpg')

# Redimensionner le fond pour l'adapter à la taille de l'écran
background_img = pygame.transform.scale(background_img, (1280, 720))

# Boucle du jeu
running = True
game_over = False
start_time = 0

while running:

    # Définir le taux de rafraîchissement
    clock.tick(60)  # 60 images par seconde

    # Dessiner l'image de fond
    screen.blit(background_img, (0, 0))
    
    show_lives(textX, textY + 40)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -3
            if event.key == pygame.K_RIGHT:
                playerX_change = 3
            if event.key == pygame.K_SPACE:
                if bullet_state == "ready":
                    bulletX = playerX
                    bulletY = playerY  # S'assurer que bulletY est réglé à playerY lors du tir
                    bullet_state = "fire"  # Changer l'état de la balle en "tir"

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                playerX_change = 0

    if not game_over:
        playerX += playerX_change
        if playerX < 0:
            playerX = 0
        elif playerX > 1230:
            playerX = 1230

        # Liste pour stocker les ennemis à supprimer
        enemies_to_remove = []

        for i in range(num_of_enemies):
            
            if enemyY[i] > 650:
                game_over = True
                start_time = pygame.time.get_ticks()  # Enregistrer l'heure de la fin de jeu
                break

            enemyX[i] += enemyX_change[i]
            if enemyX[i] <= 20:
                enemyX_change[i] = 0.3
                enemyY[i] += enemyY_change[i]
            elif enemyX[i] >= 1200:
                enemyX_change[i] = -0.3
                enemyY[i] += enemyY_change[i]

            # Trouver l'ennemi le plus proche du joueur
            closest_enemy_distance = float('inf')
            closest_enemy_index = -1
            for j in range(num_of_enemies):
                distance = abs(enemyX[j] - playerX)
                if distance < closest_enemy_distance:
                    closest_enemy_distance = distance
                    closest_enemy_index = j

            state = get_state(enemyX[i], playerX)  # Calculer l'état pour tous les ennemis
            if i == closest_enemy_index:
                # Permettre uniquement à l'ennemi le plus proche de tirer
                action = choose_action(state)
            else:
                action = 0  # Aucune action pour les autres ennemis

            # Initialiser les variables de tir
            shot = False
            hit = False

            if action == 1:  # Tirer
                shot = True
                fire_enemy_bullet(enemyX[i], enemyY[i])
                for bullet in enemy_bullets:
                    if is_collision(playerX, playerY, bullet[0], bullet[1]):
                        hit = True
                        enemy_bullets.remove(bullet)
                        break

            # Observer l'état suivant
            next_state = get_state(enemyX[i], playerX)

            # Calculer la récompense
            reward = get_reward(shot, hit)

            # Mettre à jour la table Q
            update_q_table(state, action, reward, next_state)

            collision = is_collision(enemyX[i] - 25, enemyY[i], bulletX, bulletY)
            if collision:
                bullet_state = "ready"
                bulletY = 650  # Réinitialiser la position de la balle
                score_value += 1
                enemies_to_remove.append(i)  # Ajouter l'ennemi à supprimer

            enemy(enemyX[i], enemyY[i])

        # Supprimer les ennemis marqués
        for i in sorted(enemies_to_remove, reverse=True):
            del enemyX[i]
            del enemyY[i]
            del enemyX_change[i]
            del enemyY_change[i]
            num_of_enemies -= 1  # Mettre à jour le nombre d'ennemis

        if num_of_enemies == 0:
            num_of_enemies = 36
            spawn_enemy_grid()

        if bulletY <= 0:
            bulletY = 650  # Réinitialiser bulletY à la position de départ
            bullet_state = "ready"

        if bullet_state == "fire":
            fire_bullet(bulletX, bulletY)
            bulletY -= bulletY_change

        # Mouvement des balles ennemies
        for bullet in enemy_bullets:
            bullet[1] += 4
            screen.blit(enemy_bullet_img, (bullet[0], bullet[1]))
            if bullet[1] > 700:
                enemy_bullets.remove(bullet)
            # Vérifier la collision avec les murs
            for wall in walls:
                if wall_collision(wall["rect"], bullet[0], bullet[1]):
                    wall["health"] -= 1
                    enemy_bullets.remove(bullet)
                    break
                if wall_collision(wall["rect"], bulletX, bulletY):
                    wall["health"] -= 1
                    bullet_state = "ready"
                    bulletY = 600  # Réinitialiser la position de la balle
                    break
                if wall["health"] <= 0:
                    walls.remove(wall)
                    break
            if is_collision(playerX, playerY, bullet[0], bullet[1]):
                lives -= 1  # Réduire le nombre de vies
                enemy_bullets.remove(bullet)
                playerX = 640
                playerY = 650
                playerX_change = 0
                num_of_enemies = 36
                spawn_enemy_grid()
                if lives <= 0:
                    game_over = True
                    start_time = pygame.time.get_ticks()  # Enregistrer l'heure de la fin de jeu
                break

        player(playerX, playerY)
        draw_walls()
        show_score(textX, textY)
    
    else:
        game_over_text()
        if pygame.time.get_ticks() - start_time >= 5000:  # Attendre 5 secondes
            running = False

    pygame.display.update()