import string

def print_board(board):
    for row in board:
        print(" ".join(row))

def get_move():
    while True:
        move = input("Enter move (e.g., a2 a4): ").lower()
        if len(move) == 5 and move[2] == " ":
            start_col, start_row, end_col, end_row = move[0], move[1], move[3], move[4]
            if start_col in string.ascii_lowercase[:8] and end_col in string.ascii_lowercase[:8] and                start_row in string.digits[1:9] and end_row in string.digits[1:9]:
                return (int(start_row) - 1, string.ascii_lowercase.index(start_col)),                        (int(end_row) - 1, string.ascii_lowercase.index(end_col))
        print("Invalid move format.")

def main():
    board = [
        ["R", "N", "B", "Q", "K", "B", "N", "R"],
        ["P"] * 8,
        ["."] * 8,
        ["."] * 8,
        ["."] * 8,
        ["."] * 8,
        ["p"] * 8,
        ["r", "n", "b", "q", "k", "b", "n", "r"]
    ]

    print_board(board)

    while True:
        start, end = get_move()
        board[end[0]][end[1]] = board[start[0]][start[1]]
        board[start[0]][start[1]] = "."
        print_board(board)

if __name__ == "__main__":
    main()
