import statistics


class Analyzer:
    def __init__(self, simulation):
        self.simulation = simulation
        self.global_view = simulation.network.global_view

    def num_messages(self):
        return len(self.messages())

    def num_safe_messages(self):
        return len(self.safe_messages())

    def num_unsafe_messages(self):
        return len(self.unsafe_messages())

    def num_bivalent_messages(self):
        return len(self.bivalent_messages())

    def prop_safe_messages(self):
        return float(self.num_safe_messages()) / self.num_messages()

    def safe_to_tip_length(self):
        return self.global_view.estimate().height - self.safe_tip_height()

    def safe_tip_height(self):
        if self.safe_tip():
            return self.safe_tip().height
        # Not sure I'm happy with -1 here
        return -1

    def bivalent_message_depth(self):
        max_height = max(map(lambda m: m.height, self.bivalent_messages()))
        return max_height - self.safe_tip_height()

    def bivalent_message_branching_factor(self):
        to_check = set(self.bivalent_messages())
        if self.safe_tip():
            to_check.add(self.safe_tip())

        check = to_check.pop()
        branches = 0
        num_checked = 0
        while check:
            if check in self.global_view.children:
                branches += len(self.global_view.children[check])
                num_checked += 1
            if not to_check:
                break
            check = to_check.pop()

        if num_checked == 0:
            return 0
        return branches / num_checked

    def bivalent_message_branching_factor_estimate(self):
        ''' Estimate formula taken from
        http://ozark.hendrix.edu/~ferrer/courses/335/f11/lectures/effective-branching.html '''
        return self.num_bivalent_messages() ** (1 / float(self.bivalent_message_depth()))

    def safe_tip(self):
        if not self.simulation.safe_blocks:
            return None

        return self.simulation.safe_blocks[-1]

    def messages(self):
        return self.global_view.messages

    def safe_messages(self):
        return set(self.simulation.safe_blocks)

    def bivalent_messages(self):
        return self.messages() - self.safe_messages() - self.unsafe_messages()

    def unsafe_messages(self):
        potential = self.messages() - self.safe_messages()

        if not self.safe_tip():
            return set()

        return {
            message for message in potential
            if message.height <= self.safe_tip().height
        }

    def latency_to_finality(self):
        message_data = self.simulation.message_data

        if not self.simulation.safe_blocks:
            return len(message_data)

        individual_latency = [
            message_data[message]['safe_number'] - message_data[message]['number']
            for message in self.simulation.safe_blocks
        ]

        return statistics.mean(individual_latency)

    def orphan_rate(self):
        # does not take into account that some messages exist
        # with sequence number greater than last finalized message
        num_unsafe_messages = self.num_unsafe_messages()
        num_safe_messages = self.num_safe_messages()
        if num_unsafe_messages + num_safe_messages == 0:
            return 0
        return float(num_unsafe_messages) / (num_unsafe_messages + num_safe_messages)
