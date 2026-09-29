def register_all():
    # Groups/semigroups/monoids
        
    # Applicative instances
    apply[iter] = apply(apply_iter, lambda x: iter([x]))
    apply[set] = apply(compose(set, apply_iter), lambda x: {x})
    apply[tuple] = apply(compose(tuple, apply_iter), lambda x: (x,))
    apply[list] = apply(compose(list, apply_iter), lambda x: [x])

    # Monad instances
    apply_flat[iter] = apply_flat(apply_flat_iter, lambda x: iter([x]))
    apply_flat[set] = apply_flat(compose(set, apply_flat_iter), lambda x: {x})
    apply_flat[tuple] = apply_flat(compose(tuple, apply_flat_iter), lambda x: (x,))
    apply_flat[list] = apply_flat(compose(list, apply_flat_iter), lambda x: [x])
