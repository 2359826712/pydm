import action
from arcapi import dm
import py_trees
import functools

def post_tick_handler(main_flow, snapshot_visitor, behaviour_tree):
    pass

def main_tree():
    start_game = py_trees.composites.Selector(name="启动游戏", memory=False)
    start_game.add_children([action.Start_Game(),action.Invite(),action.Collect()])

    exit_game = py_trees.composites.Selector(name="退出游戏", memory=False)
    exit_game.add_children([action.Exit_Game()])
    # 创建并行根节点
    root = py_trees.composites.Parallel(
        name="总控系统",
        policy=py_trees.common.ParallelPolicy.SuccessOnOne()
    )

    # 主业务流程
    main_flow = py_trees.composites.Sequence(name="核心流程", memory=False)
    main_flow.add_children([
        action.Set_Game_Window(), # 设置游戏窗口
        start_game,
        exit_game,
    ])

        
    root.add_children([main_flow])

    # 创建行为树
    behaviour_tree = py_trees.trees.BehaviourTree(root)
    snapshot_visitor = py_trees.visitors.SnapshotVisitor()
    
    behaviour_tree.add_post_tick_handler(
        functools.partial(
            post_tick_handler,
            main_flow,
            snapshot_visitor
        )
    )
    
    behaviour_tree.visitors.append(snapshot_visitor)
    return behaviour_tree
