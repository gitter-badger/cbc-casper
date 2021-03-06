"""The blockchain view module extends a view for blockchain data structures """
from casper.safety_oracles.clique_oracle import CliqueOracle
from casper.abstract_view import AbstractView
from casper.binary.bet import Bet
import casper.binary.binary_estimator as estimator

import random as r


class BinaryView(AbstractView):
    """A view class that also keeps track of a last_finalized_block and children"""
    def __init__(self, messages=None):
        super().__init__(messages)

        self.last_finalized_estimate = None

    def estimate(self):
        """Returns the current forkchoice in this view"""
        return estimator.get_estimate_from_latest_messages(
            self.latest_messages
        )

    def add_messages(self, showed_messages):
        """Updates views latest_messages and children based on new messages"""

        if not showed_messages:
            return

        for message in showed_messages:
            assert isinstance(message, Bet), "expected only to add a Bet!"

        # find any not-seen messages
        newly_discovered_messages = self.get_new_messages(showed_messages)

        # add these new messages to the messages in view
        self.messages.update(newly_discovered_messages)

        # update views most recently seen messages
        for message in newly_discovered_messages:
            if message.sender not in self.latest_messages:
                self.latest_messages[message.sender] = message
            elif self.latest_messages[message.sender].sequence_number < message.sequence_number:
                self.latest_messages[message.sender] = message

    def make_new_message(self, validator):
        """Make a new bet!"""
        justification = self.justification()
        estimate = self.estimate()
        if not any(self.messages):
            estimate = r.randint(0, 1)

        new_message = Bet(estimate, justification, validator)
        self.add_messages(set([new_message]))

        return new_message

    def update_safe_estimates(self, validator_set):
        """Checks safety on most recent created by this view"""
        # check estimate safety on the most
        for bet in self.latest_messages.values():
            oracle = CliqueOracle(bet, self, validator_set)
            fault_tolerance, _ = oracle.check_estimate_safety()

            if fault_tolerance > 0:
                if self.last_finalized_estimate:
                    assert not self.last_finalized_estimate.conflicts_with(bet)
                self.last_finalized_estimate = bet
                break
