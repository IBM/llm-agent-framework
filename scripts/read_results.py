# Standard
import json
import os

RESULTS_PATH = "outputs"

# Behold this function, in all of its glory


def main():
    all_results = []
    for task_dir in os.listdir(RESULTS_PATH):
        t_res_dir = os.path.join(RESULTS_PATH, task_dir)
        if os.path.isdir(t_res_dir):
            for agent_dir in os.listdir(t_res_dir):
                a_res_dir = os.path.join(t_res_dir, agent_dir)
                if os.path.isdir(a_res_dir):
                    for model_dir in os.listdir(a_res_dir):
                        m_res_dir = os.path.join(a_res_dir, model_dir)
                        if os.path.isdir(m_res_dir):
                            for filename in os.listdir(m_res_dir):
                                if filename == "output.jsonl":
                                    with open(
                                        os.path.join(m_res_dir, filename), "r"
                                    ) as f:
                                        corr, ambig, total = set(), set(), 0
                                        for l in f.readlines():
                                            data = json.loads(l)
                                            data_id = (data["question"], data["idx"])
                                            if data["is_correct"]:
                                                corr.add(data_id)
                                            if len(data["response"]) > 1:
                                                ambig.add(data_id)
                                            total += 1
                                    acc = len(corr) / total
                                    all_results.append(
                                        (
                                            task_dir,
                                            agent_dir,
                                            model_dir,
                                            ambig,
                                            corr,
                                            total,
                                            acc,
                                        )
                                    )
    all_results = sorted(all_results, key=lambda x: (x[0], x[1], x[2]))
    for res in all_results:
        task_dir, agent_dir, model_dir, ambig, corr, total, acc = res
        print(
            f" | ".join(
                [model_dir, task_dir, agent_dir, str(len(corr)), str(total), str(acc)]
            )
        )
        if agent_dir in ["cot", "direct"] and task_dir not in ["webshop"]:
            for other_res in all_results:
                if (
                    other_res[0] == task_dir
                    and other_res[1] != agent_dir
                    and other_res[2] == model_dir
                ):
                    base_corr = corr.difference(ambig)
                    other_corr = ambig.intersection(other_res[4])
                    new_corr = base_corr.union(other_corr)
                    assert not base_corr.intersection(other_corr)
                    new_acc = len(new_corr) / total
                    print(
                        f" | ".join(
                            [
                                model_dir,
                                task_dir,
                                agent_dir + "_" + other_res[1],
                                str(len(new_corr)),
                                str(total),
                                str(new_acc),
                            ]
                        )
                    )


if __name__ == "__main__":
    main()
