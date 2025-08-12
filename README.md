# Construction Crew

This is an API for users to collectively build a neural network and test it on a variety of datasets.

## Features

- [ x ] Implement JWT and account system
- [ ] Find a way to host basic datasets
- [ ] Add a way to make a new model
- [ ] Add a way to view all models
- [ ] Add a layer to a new model
- [ ] Add a way to deploy and evaluate a model
	 - [ ] Add arbitrary layer of choice
	 - [ ] Add basic experiment tracking like MLFlow or wandb
	 - [ ] Use some streams to let user know whats currently happening
	 - [ ] Add a way to download a model's state_dict
- [ ] Add a democratic way to remove a model
- [ ] Add a way to prevent spamming and basic security
- [ ] Deploy

## Tutorial

### Signup

The API distributes JWT tokens as a means of authentication.