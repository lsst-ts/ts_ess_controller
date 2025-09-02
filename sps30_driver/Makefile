CC = gcc
CFLAGS = -Wall
SRC = sps30_reader.c sps30.c sensirion_shdlc.c sensirion_uart_implementation.c sps_git_version.c
OBJ = $(SRC:.c=.o)
BIN = sps30_reader

all: $(BIN)

$(BIN): $(OBJ)
	$(CC) $(CFLAGS) -o $(BIN) $(OBJ)

clean:
	rm -f $(OBJ) $(BIN)
