from violin import checkers as vch

is_positive_int = vch.unite(*[vch.is_int, vch.is_positive])
is_not_negative_int = vch.unite(*[vch.is_int, vch.is_not_negative])
