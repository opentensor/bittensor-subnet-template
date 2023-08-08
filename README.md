# Bittensor Subnetwork Management Documentation

Welcome to the Bittensor Subnetwork Management guide. This document provides an in-depth understanding of how users can create, manage, and maintain subnetworks on the Bittensor blockchain. Through this, users will gain insights into the process of creating a subnetwork by calling the `create_subnetwork` extrinsic through the Bittensor Explorer.

## Overview

In the Bittensor blockchain, users can create a subnetwork by calling the `user_add_network` function. This function allows a user to register a new subnetwork with specific hyperparameters. In the event the total number of subnetworks reaches a predefined limit, the function will prune (remove) the subnetwork with the lowest emission score.

The emission score of a subnetwork is determined by the stake of validators in that subnetwork. The more validators staking on a subnetwork, the higher its emission score.

## Process Steps:

1. **User Call**: 
   - A user initiates the process by calling the `user_add_network` function.
   - The user must provide details such as the network modality, the immunity period, and a flag indicating if registration is allowed on the network.

2. **Validation**:
   - The system checks if the caller is a valid signed user.
   - It ensures the provided modality is valid.
   
3. **UID Allocation**:
   - Each subnetwork is assigned a unique identifier (UID).
   - If the total number of networks is less than the limit, a new UID is generated.
   - If the limit is reached, the system identifies the subnetwork with the lowest emission score for pruning, and its UID is reused.

4. **Hyperparameters Setting**:
   - Configurable hyperparameters for the network are set. These include the immunity period, network registration permission, max allowed UIDs, and max allowed validators.

5. **Network Creation**:
   - The system initializes the new subnetwork and sets various parameters.
   - An event `NetworkAdded` is emitted to notify of the successful creation of the network.

6. **Emission Calculation**:
   - Emissions for each subnet are calculated based on the stake of validators in the subnet.
   - The process ensures that each subnet receives a proportional emission based on its total stake.

7. **Pruning**:
   - If the total number of networks exceeds the limit, the `get_subnet_to_prune` function identifies the subnetwork with the lowest emission score that isn't in its immunity period. If all subnetworks are in their immunity period, the function simply picks the one with the lowest emission score.
   - The identified subnet is then removed to make space for the new subnet.

## Using Bittensor Explorer:

To create a subnetwork via the Bittensor Explorer:

1. Navigate to the Bittensor Explorer platform.
2. Look for the `create_subnetwork` extrinsic option.
3. Provide the necessary details: modality, immunity period, and registration permission.
4. Confirm and submit the transaction.
5. Once processed, you will receive a notification of the new network's creation.

## What Users Should Know:

1. **Cost**: Initiating the `user_add_network` function typically requires users to burn TAO tokens as a part of the transaction cost.
   
2. **Emission Score**: The likelihood of a subnetwork being pruned depends on its emission score, which is derived from the number of validators staking on it. Subnetworks with low stakes are more likely to be pruned.

3. **Immunity Period**: Newly created subnetworks have an immunity period during which they cannot be pruned. This period is configurable and is set during the creation process.

4. **Validator Staking**: Encouraging validators to stake on your subnetwork increases its emission score and decreases the chances of it being pruned.

5. **Hyperparameters**: These are configurable settings for the network. They play a crucial role in the operation and maintenance of the subnetwork.

6. **Updates & Monitoring**: Regularly monitoring your subnetwork's performance, stake, and emission score through the Bittensor Explorer can provide insights and help in its maintenance.

## Conclusion:

The Bittensor blockchain offers a dynamic system for managing subnetworks, allowing for expansion while ensuring that only the most supported networks thrive. By understanding the process and regularly monitoring their subnetwork's performance, users can ensure their subnetworks remain active and avoid pruning.
