import game_engine as ge


def main():
    players = ge.run_chess()
    for player in players:
        if player.check_mate:
            print(f"HAHAHA! DU TAPTE {player.name}!!")
        else:
            print(f"Gratulerer {player.name}. Du vant!!")


if __name__ == "__main__":
    main()
