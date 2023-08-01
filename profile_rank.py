from tables.profiles.FixFlipProfile import FixFlipProfile
from tables.profiles.RentProfile import RentProfile
from statistics import mean


def percentage_maxmin(max, min, value):
    return ((value - min) * 100) / (max - min)


def profile_fit_rank_rent(profile: RentProfile, listing_price, app_rate, cash_flow, coc, maintentance_spend, rent_score):

    rank_factors = [
        percentage_maxmin(profile.budget_high,
                          profile.budget_low, listing_price),
        percentage_maxmin(profile.appreciation_high,
                          profile.appreciation_low, app_rate),
        percentage_maxmin(profile.cashflow_high,
                          profile.cashflow_low, cash_flow),
        percentage_maxmin(profile.coc_high, profile.coc_low, coc),
        percentage_maxmin(profile.main_high,
                          profile.main_low, maintentance_spend),
    ]

    avg = mean(rank_factors)

    return avg * (percentage_maxmin(5, 1, rent_score)/100)


def profile_fit_rank_flip(profile: FixFlipProfile, listing_price, repair_costs, coc, market_value, flip_score):

    rank_factors = [
        percentage_maxmin(profile.budget_high,
                          profile.budget_low, listing_price),
        percentage_maxmin(profile.repair_cost_high,
                          profile.repair_cost_low, repair_costs),
        percentage_maxmin(profile.coc_high, profile.coc_low, coc),
        percentage_maxmin(profile.after_repair_high,
                          profile.after_repair_low, market_value)
    ]

    avg = mean(rank_factors)

    return avg * (percentage_maxmin(5, 1, flip_score) / 100)
