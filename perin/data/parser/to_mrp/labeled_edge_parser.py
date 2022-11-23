#!/usr/bin/env python3
# coding=utf-8

from data.parser.to_mrp.abstract_parser import AbstractParser


class LabeledEdgeParser(AbstractParser):
    def __init__(self, *args):
        super().__init__(*args)

        self.argument_roles = ['target', 'fname', 'participant', 'organizer', 'etime', 'place']
        self.event_types = ['trigger']

        self.pairs = {
            'trigger': [self.dataset.edge_label_field.vocab.stoi[item] for item in self.argument_roles]
        }

        self.argument_ids = [self.dataset.edge_label_field.vocab.stoi[arg] for arg in self.argument_roles]
        self.event_type_ids = [self.dataset.edge_label_field.vocab.stoi[e] for e in self.event_types]

    def parse(self, prediction):
        output = {}

        output["id"] = self.dataset.id_field.vocab.itos[prediction["id"].item()]
        output["nodes"] = self.create_nodes(prediction)
        output["nodes"] = self.create_anchors(prediction, output["nodes"], join_contiguous=True, at_least_one=True)
        output["nodes"] = [{"id": 0}] + output["nodes"]
        output["edges"] = self.create_edges(prediction, output["nodes"])

        return output

    def create_nodes(self, prediction):
        return [{"id": i + 1} for i, l in enumerate(prediction["labels"])]

    def create_edges(self, prediction, nodes):
        N = len(nodes)
        edge_prediction = prediction["edge presence"][:N, :N]

        edges = []

        event_nodes = []

        for target in range(1, N):
            if edge_prediction[0, target] >= 0.5:
                for j in self.argument_ids:
                    prediction['edge labels'][0, target, j] = float('-inf')
                self.create_edge(0, target, prediction, edges, nodes)
                event_nodes.append(target)
           

        for source in range(1, N):
            for target in range(1, N):
                if source == target:
                    continue
                if edge_prediction[source, target] < 0.5:
                    continue

                if source in event_nodes:
                    for j in range(7):
                        if j not in self.argument_ids:
                            prediction['edge labels'][source, target, j] = float('-inf')

                    self.create_edge(source, target, prediction, edges, nodes)

        return edges

    def get_edge_label(self, prediction, source, target):
        return self.dataset.edge_label_field.vocab.itos[prediction["edge labels"][source, target].argmax(-1).item()]
