import pygame
import time
from enum import Enum
from typing import List, Tuple

screen_width = 480
screen_height = 480
square_size = screen_width // 8
WHITE = (255, 255, 255)
LIGHT_BLUE = (72, 130, 183)

def GetSquareClicked(mouse_pos) -> Tuple[int, int]:
    square_x = mouse_pos[0] // square_size
    square_y = mouse_pos[1] // square_size
    return [square_x, square_y]

class EmptyObject:
    pass

class SquareOccupationType(Enum):
    SELF = 1
    EMPTY = 2
    FRIEND = 3
    ENEMY = 4

class PieceColor(Enum):
    WHITE = 1
    BLACK = 2

class PieceType(Enum):
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6

class Piece:
    def __init__(self, image_path: str, piece_color: PieceColor, piece_type: PieceType):
        # Load the image
        self.image = pygame.image.load(image_path)

        # Set piece color
        self.color = piece_color

        # Set piece type
        self.type = piece_type

        # Store the size
        self.size = min(square_size - 10, self.image.get_width(), self.image.get_height())

        # Scale based on size
        self.image = pygame.transform.scale(self.image, (self.size, self.size))

        # Screen position
        self.x = (square_size - self.size) // 2
        self.y = (square_size - self.size) // 2

        # Set square coord position
        self.x_coord = 0
        self.y_coord = 0

        # Set if piece has moved
        self.moved = False

        # Have captured flag
        self.captured = False
        
    def draw(self, screen: pygame.Surface):
        # Draw the piece on the screen
        if self.captured == False:
            screen.blit(self.image, (self.x, self.y))
    
    def set_square(self, x_coord: int, y_coord: int):
        # Verify input
        if x_coord > 8 or x_coord < 0 or y_coord > 8 or y_coord < 0:
            return

        # Set coords
        self.x_coord = x_coord
        self.y_coord = y_coord

        # Set x/y
        self.x = (square_size - self.size) // 2
        self.y = (square_size - self.size) // 2
        self.x += self.x_coord * square_size
        self.y += self.y_coord * square_size

        # Promote pawn if at last rank
        if self.type == PieceType.PAWN:
            if y_coord == 0 and self.color == PieceColor.WHITE:
                self.type = PieceType.QUEEN
                self.image = pygame.image.load("images/queen.png")
            elif y_coord == 7 and self.color == PieceColor.BLACK:
                self.type = PieceType.QUEEN
                self.image = pygame.image.load("images/queen1.png")

    def set_square_str(self, square: str):
        # Calculate new screen position
        x_coord = ord(square[0]) - 97
        y_coord = int(square[1]) - 1
        y_coord = 7 - y_coord
        self.set_square(x_coord, y_coord)

    def move(self, x_coord: int, y_coord: int):
        self.set_square(x_coord, y_coord)
        self.moved = True

    def set_captured(self, captured = True):
        self.captured = captured

class Board:
    def __init__(self):
        self.x_size = 8
        self.y_size = 8
        self.en_passant = EmptyObject()
        self._reset()
    
    def set_pieces(self, pieces: List[Piece]):
        self._reset()
        for piece in pieces:
            self.board[piece.x_coord][piece.y_coord] = piece

    def draw(self, screen: pygame.Surface, clicked_piece):
        # Draw the chessboard
        for row in range(self.x_size):
            for col in range(self.y_size):
                x = col * square_size
                y = row * square_size
                color = WHITE if (row + col) % 2 == 0 else LIGHT_BLUE
                pygame.draw.rect(screen, color, (x, y, square_size, square_size))

        # Draw game pieces
        for row in self.board:
            for piece in row:
                if isinstance(piece, Piece):
                    piece.draw(screen)

        # Draw highlights (don't draw if empty)
        self._determine_highlights(clicked_piece)
        self._draw_highlights(screen)

    def destination_square_type(self, x_coord: int, y_coord: int):
        for [board_x, board_y, occupation_type] in self.highlights:
            if x_coord == board_x and y_coord == board_y:
                return occupation_type
            
        return EmptyObject()

    def remove_piece_at_square(self, x_coord:int, y_coord:int):
        # Set board to None at x,y
        if x_coord < 0 or x_coord >= self.x_size or y_coord < 0 or y_coord >= self.y_size:
            return EmptyObject()
        piece = self.board[x_coord][y_coord]
        self.board[x_coord][y_coord] = None
        return piece

    def piece_clicked(self, mouse_pos):
        for row in self.board:
            for piece in row:
                if isinstance(piece, Piece):
                    if piece.image.get_rect(x=piece.x, y=piece.y).collidepoint(mouse_pos):
                        return piece

        self.clicked_piece = EmptyObject()

    def move_piece(self, piece: Piece, new_x: int, new_y: int):
        if 0 <= new_x <= 7 and 0 <= new_y <= 7:
            # Set the board
            self.board[piece.x_coord][piece.y_coord] = None
            self.board[new_x][new_y] = piece

            # Remove pawn if taking en pessant
            if not isinstance(self.en_passant, EmptyObject):
                if piece.type == PieceType.PAWN and new_x == self.en_passant[0] \
                    and new_y == self.en_passant[1]:
                    if new_y == 2:
                        self.board[new_x][3] = None
                    elif new_y == 5:
                        self.board[new_x][4] = None

            # Always reset en passant after a move
            self.en_passant = EmptyObject()

            # Set en passent if first pawn move is 2 squares
            if piece.type == PieceType.PAWN and not piece.moved:
                if piece.color == PieceColor.WHITE and new_y == 4:
                    self.en_passant = [new_x, 5]
                elif piece.color == PieceColor.BLACK and new_y == 3:
                    self.en_passant = [new_x, 2]

            # Move the piece object
            piece.move(new_x, new_y)

    def _draw_highlights(self, screen: pygame.Surface):
        if len(self.highlights) == 0:
            return

        # Add border highlighting to legal move squares
        for [x_coord, y_coord, occupation_type] in self.highlights:
            x = x_coord * square_size
            y = y_coord * square_size
            border_thickness = 4

            if occupation_type == SquareOccupationType.SELF:
                border_color = (69, 186, 76)
                center_x = x + (square_size // 2)
                center_y = y + (square_size // 2)
                radius = square_size // 2
                pygame.draw.circle(screen, border_color, (center_x, center_y), radius, border_thickness)
            elif occupation_type == SquareOccupationType.ENEMY:
                border_color = (255, 0, 0)
                center_x = x + (square_size // 2)
                center_y = y + (square_size // 2)
                radius = square_size // 2
                pygame.draw.circle(screen, border_color, (center_x, center_y), radius, border_thickness)
            elif occupation_type == SquareOccupationType.EMPTY:
                border_color = (69, 186, 76)
                inner_rect = pygame.Rect(x + border_thickness, y + border_thickness,
                                        square_size - 2 * border_thickness,
                                        square_size - 2 * border_thickness)
                pygame.draw.rect(screen, border_color, inner_rect, border_thickness)

    def _determine_highlights(self, clicked_piece):
        if isinstance(clicked_piece, EmptyObject):
            # Empty highlights if piece unset
            self.highlights = []
        elif isinstance(clicked_piece, Piece):
            # Only determine highlights the first time pice is clicked
            if len(self.highlights) == 0:
                self.highlights = self._get_legal_squares(clicked_piece)
                self.highlights.append([clicked_piece.x_coord, clicked_piece.y_coord, SquareOccupationType.SELF])

    def _get_legal_squares(self, piece: Piece) -> List[Tuple[int, int, SquareOccupationType]]:
        if piece.type == PieceType.PAWN:
            return self._get_legal_pawn_squares(piece.x_coord, piece.y_coord, piece.color, piece.moved)
        elif piece.type == PieceType.KNIGHT:
            return self._get_legal_knight_squares(piece.x_coord, piece.y_coord, piece.color)
        elif piece.type == PieceType.BISHOP:
            return self._get_legal_bishop_squares(piece.x_coord, piece.y_coord, piece.color)
        elif piece.type == PieceType.ROOK:
            return self._get_legal_rook_squares(piece.x_coord, piece.y_coord, piece.color)
        elif piece.type == PieceType.QUEEN:
            return self._get_legal_queen_squares(piece.x_coord, piece.y_coord, piece.color)
        elif piece.type == PieceType.KING:
            return self._get_legal_king_squares(piece.x_coord, piece.y_coord, piece.color)
        else:
            return []
        
    def _get_legal_pawn_squares(self, x_coord: int, y_coord: int, color: PieceColor, moved: bool) -> List[Tuple[int, int, SquareOccupationType]]:
        squares = []

        if color == PieceColor.WHITE:
            y_offset = -1
        else:
            y_offset = 1

        # Check square in front
        if self._square_type(x_coord, y_coord + y_offset, color) == SquareOccupationType.EMPTY:
            squares.append((x_coord, y_coord + y_offset, SquareOccupationType.EMPTY))

        # Check enemy squares diagonally
        if y_coord + y_offset >= 0 and y_coord + y_offset <= 7:
            if self._square_type(x_coord - 1, y_coord + y_offset, color) == SquareOccupationType.ENEMY or \
                [x_coord - 1, y_coord + y_offset] == self.en_passant:
                squares.append((x_coord - 1, y_coord + y_offset, SquareOccupationType.ENEMY))
            if self._square_type(x_coord + 1, y_coord + y_offset, color) == SquareOccupationType.ENEMY or \
                [x_coord + 1, y_coord + y_offset] == self.en_passant:
                squares.append((x_coord + 1, y_coord + y_offset, SquareOccupationType.ENEMY))

        # If hasn't moved then allow moving two squares
        if not moved and self._square_type(x_coord, y_coord + (y_offset * 2), color) == SquareOccupationType.EMPTY:
            squares.append((x_coord, y_coord + (y_offset * 2), SquareOccupationType.EMPTY))

        return squares
    
    def _get_legal_knight_squares(self, x_coord: int, y_coord: int, color: PieceColor) -> List[Tuple[int, int, SquareOccupationType]]:
        squares = []

        possible_moves = [
            (x_coord + 2, y_coord + 1),
            (x_coord + 2, y_coord - 1),
            (x_coord - 2, y_coord + 1),
            (x_coord - 2, y_coord - 1),
            (x_coord + 1, y_coord + 2),
            (x_coord + 1, y_coord - 2),
            (x_coord - 1, y_coord + 2),
            (x_coord - 1, y_coord - 2)
        ]

        for [new_x, new_y] in possible_moves:
            if 0 <= new_x <= 7 and 0 <= new_y <= 7:
                destination_type = self._square_type(new_x, new_y, color)
                if destination_type == SquareOccupationType.EMPTY or destination_type == SquareOccupationType.ENEMY:
                    squares.append([new_x, new_y, destination_type])

        return squares
    
    def _get_legal_bishop_squares(self, x_coord: int, y_coord: int, color: PieceColor) -> List[Tuple[int, int, SquareOccupationType]]:
        squares = []
        directions = [[-1, -1], [-1, 1], [1, -1], [1, 1]]

        for direction in directions:
            current_x = x_coord
            current_y = y_coord

            while (True):
                current_x += direction[0]
                current_y += direction[1]

                if (0 > current_x or current_x > 7 or 0 > current_y or current_y > 7):
                    break

                square_type = self._square_type(current_x, current_y, color)

                if square_type == SquareOccupationType.FRIEND:
                    break

                squares.append([current_x, current_y, square_type])

                if square_type == SquareOccupationType.ENEMY:
                    break

        return squares

    def _get_legal_rook_squares(self, x_coord: int, y_coord: int, color: PieceColor) -> List[Tuple[int, int, SquareOccupationType]]:
        squares = []
        directions = [[-1, 0], [0, 1], [1, 0], [0, -1]]

        for direction in directions:
            current_x = x_coord
            current_y = y_coord

            while (True):
                current_x += direction[0]
                current_y += direction[1]

                if (0 > current_x or current_x > 7 or 0 > current_y or current_y > 7):
                    break

                square_type = self._square_type(current_x, current_y, color)

                if square_type == SquareOccupationType.FRIEND:
                    break

                squares.append([current_x, current_y, square_type])

                if square_type == SquareOccupationType.ENEMY:
                    break

        return squares

    def _get_legal_queen_squares(self, x_coord: int, y_coord: int, color: PieceColor) -> List[Tuple[int, int, SquareOccupationType]]:
        squares = []
        directions = []

        for i in range(-1, 2):
            for j in range (-1, 2):
                directions.append([i, j])

        for direction in directions:
            current_x = x_coord
            current_y = y_coord

            while (True):
                current_x += direction[0]
                current_y += direction[1]

                if (0 > current_x or current_x > 7 or 0 > current_y or current_y > 7):
                    break

                square_type = self._square_type(current_x, current_y, color)

                if square_type == SquareOccupationType.FRIEND:
                    break

                squares.append([current_x, current_y, square_type])

                if square_type == SquareOccupationType.ENEMY:
                    break

        return squares

    def _get_legal_king_squares(self, x_coord: int, y_coord: int, color: PieceColor) -> List[Tuple[int, int, SquareOccupationType]]:
        squares = []
        directions = []

        for i in range(-1, 2):
            for j in range (-1, 2):
                directions.append([i, j])

        for direction in directions:
            current_x = x_coord + direction[0]
            current_y = y_coord + direction[1]

            if (0 > current_x or current_x > 7 or 0 > current_y or current_y > 7):
                continue

            square_type = self._square_type(current_x, current_y, color)

            if square_type == SquareOccupationType.FRIEND:
                continue

            squares.append([current_x, current_y, square_type])

        return squares

    def _square_type(self, x_coord: int, y_coord: int, friendly_color: PieceColor) -> SquareOccupationType:
        if 0 > x_coord or x_coord > 7 or 0 > y_coord or y_coord > 7:
            return
        
        other_piece = self.board[x_coord][y_coord]

        if other_piece is None:
            return SquareOccupationType.EMPTY
        
        if isinstance(other_piece, Piece) and other_piece.color != friendly_color:
            return SquareOccupationType.ENEMY
        
        return SquareOccupationType.FRIEND

    def _reset(self):
        self.board = [[None] * self.x_size for _ in range(self.y_size)]
        self.highlights = []

class ChessGame:
    def __init__(self):
        # Setup white pieces
        pawn_a_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_b_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_c_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_d_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_e_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_f_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_g_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        pawn_h_white = Piece("images/pawn.png", PieceColor.WHITE, PieceType.PAWN)
        knight_b_white = Piece("images/knight.png", PieceColor.WHITE, PieceType.KNIGHT)
        knight_g_white = Piece("images/knight.png", PieceColor.WHITE, PieceType.KNIGHT)
        bishop_c_white = Piece("images/bishop.png", PieceColor.WHITE, PieceType.BISHOP)
        bishop_f_white = Piece("images/bishop.png", PieceColor.WHITE, PieceType.BISHOP)
        rook_a_white = Piece("images/rook.png", PieceColor.WHITE, PieceType.ROOK)
        rook_h_white = Piece("images/rook.png", PieceColor.WHITE, PieceType.ROOK)
        queen_white = Piece("images/queen.png", PieceColor.WHITE, PieceType.QUEEN)
        king_white = Piece("images/king.png", PieceColor.WHITE, PieceType.KING)

        # Set white piece positions
        pawn_a_white.set_square_str("a2")
        pawn_b_white.set_square_str("b2")
        pawn_c_white.set_square_str("c2")
        pawn_d_white.set_square_str("d2")
        pawn_e_white.set_square_str("e2")
        pawn_f_white.set_square_str("f2")
        pawn_g_white.set_square_str("g2")
        pawn_h_white.set_square_str("h2")
        knight_b_white.set_square_str("b1")
        knight_g_white.set_square_str("g1")
        bishop_c_white.set_square_str("c1")
        bishop_f_white.set_square_str("f1")
        rook_a_white.set_square_str("a1")
        rook_h_white.set_square_str("h1")
        queen_white.set_square_str("d1")
        king_white.set_square_str("e1")
        
        # Setup black pieces
        pawn_a_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_b_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_c_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_d_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_e_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_f_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_g_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        pawn_h_black = Piece("images/pawn1.png", PieceColor.BLACK, PieceType.PAWN)
        knight_b_black = Piece("images/knight1.png", PieceColor.BLACK, PieceType.KNIGHT)
        knight_g_black = Piece("images/knight1.png", PieceColor.BLACK, PieceType.KNIGHT)
        bishop_c_black = Piece("images/bishop1.png", PieceColor.BLACK, PieceType.BISHOP)
        bishop_f_black = Piece("images/bishop1.png", PieceColor.BLACK, PieceType.BISHOP)
        rook_a_black = Piece("images/rook1.png", PieceColor.BLACK, PieceType.ROOK)
        rook_h_black = Piece("images/rook1.png", PieceColor.BLACK, PieceType.ROOK)
        queen_black = Piece("images/queen1.png", PieceColor.BLACK, PieceType.QUEEN)
        king_black = Piece("images/king1.png", PieceColor.BLACK, PieceType.KING)

        # Set black piece positions
        pawn_a_black.set_square_str("a7")
        pawn_b_black.set_square_str("b7")
        pawn_c_black.set_square_str("c7")
        pawn_d_black.set_square_str("d7")
        pawn_e_black.set_square_str("e7")
        pawn_f_black.set_square_str("f7")
        pawn_g_black.set_square_str("g7")
        pawn_h_black.set_square_str("h7")
        knight_b_black.set_square_str("b8")
        knight_g_black.set_square_str("g8")
        bishop_c_black.set_square_str("c8")
        bishop_f_black.set_square_str("f8")
        rook_a_black.set_square_str("a8")
        rook_h_black.set_square_str("h8")
        queen_black.set_square_str("d8")
        king_black.set_square_str("e8")

        game_pieces = [pawn_a_white, pawn_b_white, pawn_c_white, pawn_d_white,
                       pawn_e_white, pawn_f_white, pawn_g_white, pawn_h_white,
                       knight_b_white, knight_g_white, bishop_c_white, bishop_f_white, 
                       rook_a_white, rook_h_white, queen_white, king_white,
                       pawn_a_black, pawn_b_black, pawn_c_black, pawn_d_black,
                       pawn_e_black, pawn_f_black, pawn_g_black, pawn_h_black,
                       knight_b_black, knight_g_black, bishop_c_black, bishop_f_black, 
                       rook_a_black, rook_h_black, queen_black, king_black]
        
        self.game_board = Board()
        self.game_board.set_pieces(game_pieces)

        self.turn = PieceColor.WHITE

        self.clicked_piece = EmptyObject()
        
    def draw(self, screen: pygame.SurfaceType): 
        # Draw board and highlights
        self.game_board.draw(screen, self.clicked_piece)

    def mouse_left_click(self, mouse_pos):
        # Set new square for piece
        if isinstance(self.clicked_piece, Piece):
            [x_coord, y_coord] = GetSquareClicked(mouse_pos)
            destination_square_type = self.game_board.destination_square_type(x_coord, y_coord)

            if isinstance(destination_square_type, SquareOccupationType):
                self.game_board.move_piece(self.clicked_piece, x_coord, y_coord)

                # Change turn
                if self.turn == PieceColor.WHITE:
                    self.turn = PieceColor.BLACK
                else:
                    self.turn = PieceColor.WHITE

            # Reset clicked_piece
            self.clicked_piece = EmptyObject()

        # Get piece user clicked
        elif isinstance(self.clicked_piece, EmptyObject):
            clicked = self.game_board.piece_clicked(mouse_pos)
            if isinstance(clicked, Piece) and clicked.color == self.turn:
                self.clicked_piece = clicked

    def _remove_piece(self, x_coord: int, y_coord: int):
        piece = self.game_board.remove_piece_at_square(x_coord, y_coord)

        if isinstance(piece, Piece):
            piece.set_captured()

def main():
    # Initialize Pygame
    pygame.init()

    # Set up the display
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Chess Board")

    # Setup Chess game
    chess_game = ChessGame()

    # Game loop
    running = True

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    mouse_pos = pygame.mouse.get_pos()
                    chess_game.mouse_left_click(mouse_pos)

                elif event.button == 3: # Right mouse button
                    print("Right mouse button clicked")

        # Clear the screen
        screen.fill(WHITE)

        # Draw board and pieces
        chess_game.draw(screen)

        # Update the display
        pygame.display.flip()

    # Quit the game
    pygame.quit()

main()