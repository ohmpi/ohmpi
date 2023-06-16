import matplotlib.pyplot as plt
import numpy as np
from ohmpi.utils import parse_log
import matplotlib


def plot_exec_log(exec_log,names=None,last_session=True):  # TODO: select session id instead of last session (if -1 : last)
    time, process_id, tag, msg, session = parse_log(exec_log)
    print(session)
    if last_session:
        time, process_id, tag, msg = time[session==max(session)], process_id[session==max(session)], tag[session==max(session)], msg[session==max(session)]
    events = msg[tag == 'EVENT']
    print(time)
    category, name, state, time = np.empty(events.shape[0]).astype(str), np.empty(events.shape[0]).astype(str), \
        np.empty(events.shape[0]).astype(str), np.empty(events.shape[0]).astype(str)

    for i, event in enumerate(events):
        category[i] = event.split("\t")[0]
        name[i] = event.split("\t")[1]
        state[i] = event.split("\t")[2]
        time[i] = event.split("\t")[3].replace('\n','')
    time = time.astype(np.datetime64)
    state = state[time.argsort()]
    category = category[time.argsort()]
    name = name[time.argsort()]
    time = np.sort(time)

    if names is None:
        names = dict.fromkeys(np.unique(category))
        for cat in np.unique(category):
            names[cat] = np.array(np.unique(name[category == cat]))

    fig, ax = plt.subplots(len(names.keys()),sharex=True)
    if not isinstance(ax,np.ndarray):
        ax = np.array([ax])
    for i, cat in enumerate(names.keys()):
        y = 0
        for j, n in enumerate(names[cat]):
            cmap = matplotlib.cm.get_cmap('tab20')
            colors = [cmap(c/len(names[cat])) for c in range(len(names[cat]))]
            event_ids = np.where((name == n) & (category == cat))[0]
            y += 1
            ax[i].set_title(cat)
            label = True
            for k, id in enumerate(event_ids[:-1]):
                if state[event_ids[k]] == 'begin' and state[event_ids[k+1]] == 'end':
                    if label:
                        ax[i].fill_betweenx([y,y+1],time[event_ids[k]],time[event_ids[k+1]],color=colors[j],label=n)
                        label=False
                    else:
                        ax[i].fill_betweenx([y, y + 1], time[event_ids[k]], time[event_ids[k + 1]], color=colors[j])
        y_labels = names[cat]
        y_label_pos = np.arange(len(names[cat]))+1.5

        ax[i].set_yticks(y_label_pos)
        ax[i].set_yticklabels(y_labels)
        ax[i].legend()
    plt.show()

