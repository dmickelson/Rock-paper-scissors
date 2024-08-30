def check_if_abbey(opponent_history, my_moves):
    if len(my_moves) < 2:
        return True

    play_order = {
        "RR": 0, "RP": 0, "RS": 0,
        "PR": 0, "PP": 0, "PS": 0,
        "SR": 0, "SP": 0, "SS": 0,
    }

    for i in range(len(my_moves) - 1):
        key = my_moves[i] + my_moves[i+1]
        if key in play_order:
            play_order[key] += 1

    last_two = "".join(my_moves[-2:])
    potential_plays = [last_two[1] + "R", last_two[1] + "P", last_two[1] + "S"]

    sub_order = {k: play_order[k] for k in potential_plays if k in play_order}
    if not sub_order:
        return False

    prediction = max(sub_order, key=sub_order.get)[-1:]
    expected_move = counter_move(prediction)

    if opponent_history[-1] == expected_move:
        print("Playing Against Abbey")
        return True
    else:
        print("Not playing against Abbey")
        print(f"Expected move {expected_move} but got {opponent_history[-1]}")
        return False


def abbey_counter(my_moves):
    play_order = {
        "RR": 0, "RP": 0, "RS": 0,
        "PR": 0, "PP": 0, "PS": 0,
        "SR": 0, "SP": 0, "SS": 0,
    }

    for i in range(len(my_moves) - 1):
        key = my_moves[i] + my_moves[i+1]
        if key in play_order:
            play_order[key] += 1

    last_two = "".join(my_moves[-2:])
    potential_plays = [last_two[1] + "R", last_two[1] + "P", last_two[1] + "S"]

    sub_order = {k: play_order[k] for k in potential_plays if k in play_order}
    if not sub_order:
        return random.choice(['R', 'P', 'S'])

    prediction = max(sub_order, key=sub_order.get)[-1:]
    abbey_move = counter_move(prediction)
    print(f"Abbey prediction {abbey_move}")
    my_counter = counter_move(abbey_move)
    print(f"I played {my_counter}")
    return counter_move(abbey_move)


def counter_move(move):
    return {'R': 'P', 'P': 'S', 'S': 'R'}[move]
