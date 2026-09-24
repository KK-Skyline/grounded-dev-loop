# 据实落地：短例

## Debug：测试红

```text
goal: 让 test_cart_total 过，不改其它计价规则
mode: debug
working-set: cart.py:total, tests/test_cart.py:test_cart_total
evidence: pytest tests/test_cart.py::test_cart_total  → AssertionError 19 != 20（本回合）
```

做：只改 `total` 里导致 19 的那条分支。  
不做：改 expected 成 19；顺手重写折扣模块；给缺字段填 0。  
验证：同一条测试绿；若 `total` 被其它测试共用，跑 `tests/test_cart.py`。

## Implement：一个小行为

```text
goal: POST /items 在重名时返回 409
mode: implement
working-set: items_router.py, items_service.py, tests/test_items_create.py
evidence: 当前重名返回 200（本回合 curl 或已有测试）
```

做：冲突分支 + 一条断言 409 的测试。  
不做：顺手加 422 的全新校验框架；改无关 list 接口。  
验证：那条创建测试或 curl；邻居仅当共享 error mapper 时才跑。

## 长对话压缩后

不要：「根据我们之前的结论，根因是 X，继续改 Y。」  
要：重跑当时的失败命令或重读工作集里的当前文件，用新输出填 `evidence`，再决定是否还改 Y。

## 两次落空

同一 `pytest …::test_cart_total` 已两次改完仍红：停止再猜。画出 `request → service → total → tax`，标谁是权威、有没有第二处改价。第三刀必须打在图上的一个节点。
