use std::iter;
use std::sync::Arc;

use rand::distributions::WeightedIndex;
use rand_distr::Distribution;

use non_dominated_sort::{non_dominated_sort, DominanceOrd};

use crate::configure::Config;
use crate::evolution::{Genome, Phenome};
use crate::increment_epoch_counter;
use crate::observer::Observer;
use crate::ontogenesis::Develop;
use crate::util::random::hash_seed_rng;

pub struct Roulette<E: Develop<P>, P: Phenome + Genome + 'static, D: DominanceOrd<P>> {
    pub population: Vec<P>,
    pub config: Arc<Config>,
    pub observer: Observer<P>,
    pub evaluator: E,
    pub iteration: usize,
    pub dominance_order: D,
}

impl<E: Develop<P>, P: Phenome + Genome + 'static, D: DominanceOrd<P>> Roulette<E, P, D> {
    pub fn new(config: &Config, observer: Observer<P>, evaluator: E, dominance_order: D) -> Self {
        let population = (0..config.pop_size)
            .map(|i| P::random(&config, i))
            .collect();

        Self {
            population,
            config: Arc::new(config.clone()),
            iteration: 0,
            observer,
            evaluator,
            dominance_order,
        }
    }

    pub fn evolve(self) -> Self {
        let Self {
            population,
            observer,
            mut evaluator,
            config,
            iteration,
            dominance_order,
        } = self;

        let mut rng = hash_seed_rng(&population);
        // measure and assign fitness scores to entire population
        let mut population = evaluator
            .development_pipeline(population.into_iter())
            .into_iter()
            .map(|p| evaluator.apply_fitness_function(p))
            .collect::<Vec<P>>();
        // we're going to need to clone the population to send to the observer, anyway
        // so we might as well do that now. this lets us get around certain awkward
        // lifetime constraints imposed on us by the `Front` struct.
        let cloned_population = population.clone();

        // we want the odds of breeding to be relative to the front on which the
        // individuals occur. the lower the front, the better the chances.
        let mut cur_weight = 1.0;
        let mut indices_weights: Vec<(usize, f64)> = Vec::new();
        let mut elite_fronts: Vec<Vec<usize>> = Vec::new();
        // let mut parent_indices = Vec::new();
        // let mut parents_needed = config.pop_size / 2;
        {
            let mut front = non_dominated_sort(&cloned_population, &dominance_order);
            elite_fronts.push(front.current_front_indices().to_vec());
            while !front.is_empty() {
                front.current_front_indices().iter().for_each(|i| {
                    population[*i].set_front(front.rank());
                    indices_weights.push((*i, cur_weight));
                    // if parents_needed > 0 {
                    //     parent_indices.push(*i);
                    //     parents_needed -= 1;
                    // }
                });

                front = front.next_front();
                cur_weight *= config.roulette.weight_decay;
            }
        }
        indices_weights.sort_by_key(|p| p.0);
        let (indices, weights): (Vec<usize>, Vec<f64>) = indices_weights.iter().cloned().unzip();
        // Now, create a weighted random distribution where the odds of an index being
        // drawn are proportionate to the rank of the front on which the creature that
        // index points to appears.
        let dist = WeightedIndex::new(&weights).expect("failed to create weighted index");

        // send the old copy of the population to the observer
        // these have each been marked with the rank of their front
        population.into_iter().for_each(|p| {
            observer.observe(p);
        });

        let mut new_population: Vec<P> = Vec::new();

        // Transfer the elites -- the members of the 0th front -- to the
        // new population as-is.
        for idxs in &elite_fronts {
            for idx in idxs.iter() {
                new_population.push(cloned_population[*idx].clone());
            }
        }

        // let all_parents = parent_indices
        //     .into_iter()
        //     .map(|i| &cloned_population[i])
        //     .collect::<Vec<&P>>();
        while new_population.len() < config.pop_size {
            let parents: Vec<&P> = iter::repeat(())
                // FIXME: define parentage numbers in separate selection method sections
                .take(config.tournament.num_parents)
                .map(|()| indices[dist.sample(&mut rng)])
                .map(|i| &cloned_population[i])
                .collect::<Vec<&P>>();

            // let parents = iter::repeat(())
            //     .take(config.num_parents)
            //     .map(|()| all_parents[rng.gen::<usize>() % all_parents.len()])
            //     .collect::<Vec<&P>>();

            let child: P = Genome::mate(&parents, &config);
            new_population.push(child)
        }

        increment_epoch_counter();

        Self {
            population: new_population,
            config,
            observer,
            evaluator,
            iteration: iteration + 1,
            dominance_order,
        }
    }
}
