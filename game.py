from sympy.stats import Coin, Die, FiniteRV, E, P, sample


F = Die('Fair', 4)
L = FiniteRV('Loaded', {1: 0.4, 2: 0.3, 3: 0.2, 4: 0.1})
dice_pick = FiniteRV('Pick', {0: 0.5, 1: 0.5})
die = [F, L]
total = 0

rounds = 1
while True:
    # To start the game, we pick a dice randomly
    D = die[sample(dice_pick)]
    # Roll the dice
    result = sample(D)
    # Decide if you want to stay or switch
    decisions = ['stay', 'switch']
    decision = decisions[1]
    if decision == 'switch':
        if D == F:
            D = L
        else:
            D = F
    # Your friend makes a bet
    friends_bets = ['low', 'high']
    friends_bet = friends_bets[0]
    # Roll the die and win $50 or lose $30 based on the friend's bet
    final_result = sample(D)
    if (final_result > 2 and friends_bet == 'high') or (final_result <= 2 and friends_bet == 'low'):
        # We lose $30
        total -= 30
    else:
        # We win $50
        total += 50
    print(f"My money: {total}")
    rounds += 1
