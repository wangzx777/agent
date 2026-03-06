import requests
import json

url = "http://192.168.180.95:8080/chat/api/019bb239-0107-7fb1-b50c-f4a12d9a068d/chat/completions"

headers = {
    "Authorization": "Bearer application-f850846002fee63261f0722b4385b038",
    "Content-Type": "application/json"
}

data = {
    "model": "gpt-3.5-turbo",
    "messages": [
    {
      "role": "user",
      "content": "## 专家角色\n数据库专家\n\n## 智能体提示词\n你是一个专业的智能数据库助手，具备以下核心能力：\n\n## 1. 查询理解与推理\n- 深度理解用户的查询意图，包括隐含需求和上下文关联\n- 对于模糊或不完整的查询，主动推断可能的查询目标\n- 识别查询中的关键实体、时间范围、条件等要素\n\n## 2. SQL查询构建\n- 根据表结构和用户需求，构建准确、高效的SQL查询语句\n- 合理使用JOIN、WHERE、GROUP BY、HAVING等SQL子句\n- 优化查询性能，避免全表扫描，合理使用索引\n- 添加适当的LIMIT限制，避免返回过多数据\n\n## 3. 结果分析与解释\n- 对查询结果进行深入分析，提取关键信息\n- 用清晰、易懂的语言解释查询结果\n- 如果结果为空，分析可能原因并提供改进建议\n- 识别数据中的模式、趋势和异常\n\n## 4. 智能建议\n- 基于查询结果，主动提供相关的后续查询建议\n- 识别用户可能感兴趣的其他数据维度\n- 提供数据可视化的建议（如适用）\n\n## 5. 交互优化\n- 使用自然、友好的语言与用户交流\n- 适时询问澄清问题，确保理解准确\n- 提供多种查询方案供用户选择\n\n记住：你的目标是成为用户的智能数据助手，帮助他们发现数据的价值，而不仅仅是执行SQL查询。\n\n## 用户问题\n2024年绩效为s的都有哪些人\n\n## 背景信息\n\n\n\n\n\n## 可用工具\n- execute_query: 执行安全的 SQL 查询语句（仅限 SELECT）\n\n安全措施：\n    - 严格验证 SQL 语法\n    - 只允许 SELECT 语句\n    - 禁止所有修改数据的操作（INSERT, UPDATE, DELETE, DROP, ALTER 等）\n    - 限制查询长度和结果行数\n    - 限制执行时间\n    - 防止 SQL 注入\n    \n参数:\n    sql (str): 要执行的 SQL 查询语句\n    \n返回:\n    List[Dict]: 查询结果，每个字典代表一行数据，键为列名，值为对应的数据\n    \n示例：\n    execute_query(\"SELECT * FROM users LIMIT 5\")\n    execute_query(\"SELECT name, email FROM customers WHERE age > 18\")\n- get_table_schema: 获取指定表的完整结构信息（列名、数据类型、是否可为空、默认值、字段注释等）\n\n参数:\n    table_name (str): 表名\n    \n返回:\n    Dict: 包含表名和详细列信息的字典，每列包含：\n        - column_name: 列名\n        - data_type: 数据类型  \n        - is_nullable: 是否可为空 (YES/NO)\n        - column_default: 默认值\n        - column_comment: 字段注释（中文说明）\n        - extra: 额外信息（如 auto_increment）\n    \n示例：\n    get_table_schema(\"basic_info\")\n- list_tables: 列出数据库中的所有表\n\n返回:\n    List[str]: 表名列表\n    \n示例：\n    list_tables()\n\n\n\n\n\n\n\n## 工具调用说明\n如果需要调用工具，请在回答中使用以下格式:\ncall_tool(\"tool_name\", {\"param1\": \"value1\", \"param2\": \"value2\"})\n例如: call_tool(\"list_tables\", {})\n⚠️ 重要：每次只能调用一个工具，不要在同一回答中调用多个工具。\n如果需要调用多个工具，请分多次回答，每次调用一个工具。\n\n## 结束标签说明\n⚠️ 重要：只有在你确定已经完全解决了用户的问题，并且不需要再调用任何工具或进行更多操作时，才可以在回复末尾添加 <end></end> 标签。\n\n✅ 正确的结束时机包括：\n- 你已经直接回答了用户的问题（无需工具调用）\n- 你已经调用了必要的工具，并基于工具返回的结果给出了完整的回答\n- 所有相关任务都已完成，用户的问题得到了彻底解决\n\n❌ 不要过早结束的情况：\n- 你还需要调用工具来获取信息\n- 你刚刚调用了工具但还没有看到工具的执行结果\n- 用户的问题还没有得到完整解答\n\n📝 示例：\n这是我的完整回答，已经解决了用户的所有问题。<end></end>\n\n## 历史记录\n第0轮:\ncall_tool(\"get_table_schema\", {\"table_name\": \"performance_records\"})\n\n第0轮:\ncall_tool(\"execute_query\", {\"sql\": \"SELECT * FROM performance_records WHERE evaluation_year = '2024' AND evaluation_result = 'S' LIMIT 50\"})\n\n第0轮:\n根据已收集的信息，当前表 `performance_records` 中的字段 `evaluation_year` 和 `evaluation_result` 分别存储了考核年份和考核结果。我们已经执行了查询以获取 `2024` 年绩效为 `S` 的记录，但未返回任何数据。\n\n为了进一步分析，我们需要确认是否还有其他表可能存储了相关的绩效数据，例如员工编号 `employee_id` 是否关联到其他表（如员工基本信息表）。因此，我们需要列出所有表以查看是否存在与员工绩效相关的其他表。\n\ncall_tool(\"list_tables\", {})\n\n第0轮:\n根据用户的问题\"2024年绩效为S的都有哪些人\"，我们已经收集了以下信息：\n1. `performance_records`表的结构：包含`employee_id`（员工编号）、`evaluation_result`（考核结果）、`evaluation_year`（考核年份）等字段。\n2. 查询了`performance_records`表中`evaluation_year = '2024'`且`evaluation_result = 'S'`的记录，但返回了空数据。\n3. 数据库中存在多个与员工信息相关的表，例如`basic_info`、`work_experience`等，可能包含员工姓名、编号等信息。\n\n由于`performance_records`表中没有返回数据，我们需要进一步确认是否存在其他表存储了2024年的绩效信息，或是否存在其他相关表可以通过员工编号`employee_id`关联以验证数据来源。因此，我们首先需要查看`basic_info`表的结构，以了解员工编号和姓名是否可以关联查询。\n\ncall_tool(\"get_table_schema\", {\"table_name\": \"basic_info\"})\n\n第0轮:\n根据用户的问题\"2024年绩效为S的都有哪些人\"，我们已经收集了以下关键信息：\n\n1. **`performance_records`表结构**：\n   - 包含字段：`employee_id`（员工编号）、`evaluation_result`（考核结果）、`evaluation_year`（考核年份）等。\n   - 已执行查询 `SELECT * FROM performance_records WHERE evaluation_year = '2024' AND evaluation_result = 'S' LIMIT 50`，但返回了空数据。\n   \n2. **数据库中存在`basic_info`表**：\n   - 包含员工基本信息，如`employee_id`（员工编号）、`employee_name`（员工姓名）等，可用于关联查询。\n   - 该表的结构已获取。\n\n3. **数据库中存在多个与员工信息相关的表**，例如`work_experience`、`education_history`等，但目前尚未确认是否与绩效数据相关。\n\n由于`performance_records`表中未返回任何符合条件的记录，可能存在以下几种情况：\n- 数据尚未录入；\n- `evaluation_year`字段存储的是年份以外的数据（例如字符串格式不符合条件）；\n- `employee_id`字段与主数据表（如`basic_info`）的关联方式不同。\n\n为了进一步确认是否存在其他数据来源，我们可以通过以下方式验证：\n1. 确认`basic_info`表中是否包含所有员工的记录，并检查是否能够通过`employee_id`关联到`performance_records`表。\n2. 检查`performance_records`表中是否存在2024年的绩效数据，但未标记为\"S\"。\n\n因此，下一步我们将执行一个联合查询，将`performance_records`和`basic_info`表通过`employee_id`进行关联，以查看是否存在匹配的员工记录。如果查询结果仍然为空，我们将进一步检查是否存在其他表存储了绩效数据。\n\ncall_tool(\"execute_query\", {\"sql\": \"SELECT b.employee_id, b.employee_name, p.evaluation_result, p.evaluation_year FROM basic_info b LEFT JOIN performance_records p ON b.employee_id = p.employee_id WHERE p.evaluation_year = '2024' AND p.evaluation_result = 'S' LIMIT 50\"})\n\n第1轮:\n根据目前的查询结果和数据情况，`performance_records`表中并未返回2024年绩效为\"S\"的任何记录。这可能意味着以下几种情况：\n\n1. **数据尚未录入**：2024年的绩效评估结果尚未被录入到系统中。\n2. **数据存储问题**：`evaluation_year`或`evaluation_result`字段的值可能不符合预期的格式，例如存储的是其他字符而非\"2024\"或\"S\"。\n3. **数据不存在**：2024年没有任何员工的绩效评估结果为\"S\"。\n\n为了进一步确认，建议采取以下步骤：\n1. 检查`performance_records`表中是否包含2024年的绩效数据（即使不是\"S\"）。\n2. 验证`evaluation_result`字段中是否包含\"S\"值。\n3. 检查`employee_id`字段的关联性，确保与`basic_info`表的关联逻辑正确。\n\n因此，下一步我们将执行一个更广泛的查询，以检查`performance_records`表中是否存在2024年的绩效数据，而不论其评估结果为何。\n\ncall_tool(\"execute_query\", {\"sql\": \"SELECT * FROM performance_records WHERE evaluation_year = '2024' LIMIT 50\"})\n\n第2轮:\n根据目前的查询结果和数据情况，`performance_records`表中并未返回2024年的任何绩效数据，这意味着以下几种可能性：\n\n1. **数据尚未录入**：2024年的绩效评估结果可能尚未被录入到系统中。\n2. **数据存储问题**：`evaluation_year`字段可能存储的不是\"2024\"或格式不一致（例如为整数、日期格式等）。\n3. **数据不存在**：2024年可能确实没有任何员工的绩效记录，或者没有员工获得\"S\"级评价。\n\n为了解决这个问题，我们需要进一步验证以下几点：\n1. 确认`performance_records`表中是否存在任何绩效数据。\n2. 检查`evaluation_year`字段的值是否为字符串\"2024\"，或者是否存在其他格式（例如整数或日期）。\n3. 验证`evaluation_result`字段中是否存在\"S\"值。\n\n下一步，我们将执行一个查询，以检查`performance_records`表中是否存在任何数据，并检查`evaluation_year`和`evaluation_result`字段的内容。\n\ncall_tool(\"execute_query\", {\"sql\": \"SELECT DISTINCT evaluation_year, evaluation_result FROM performance_records LIMIT 50\"})\n\n第3轮:\n根据最新的查询结果，`performance_records`表中存在2024年的绩效记录，但绩效结果字段 `evaluation_result` 的值并不是\"S\"，而是\"S卓越\"。这表明字段值可能包含了更详细的描述性文本，而不是单个字母\"S\"。\n\n为了获取2024年绩效为\"S\"（或\"S卓越\"）的员工信息，我们应修改查询条件，将 `evaluation_result = 'S'` 替换为 `evaluation_result LIKE '%S%'`，以匹配包含\"S\"的所有记录（例如\"S卓越\"）。\n\n因此，下一步我们将重新执行查询，以获取2024年绩效包含\"S\"的员工信息，并将这些信息与 `basic_info` 表关联，以获取员工的姓名。\n\ncall_tool(\"execute_query\", {\"sql\": \"SELECT b.employee_id, b.employee_name, p.evaluation_result, p.evaluation_year FROM basic_info b LEFT JOIN performance_records p ON b.employee_id = p.employee_id WHERE p.evaluation_year = '2024' AND p.evaluation_result LIKE '%S%' LIMIT 50\"})\n\n第4轮:\n根据最新的查询结果和分析，我们得出以下结论：\n\n1. `performance_records`表中包含2024年的绩效记录，但`evaluation_result`字段的值为\"B良好\"、\"C合格\"、\"D待改进\"等，并没有\"S\"或包含\"S\"的记录。\n2. 尽管我们尝试通过模糊匹配（`LIKE '%S%'`）查找，但依然没有结果返回，这说明2024年确实没有任何员工获得\"S\"级的绩效评价。\n3. 在表中，2024年记录中最高的绩效等级为\"A优秀\"，而\"S卓越\"只出现在2021年、2022年和2023年。\n\n### 可能的原因：\n- **2024年没有员工获得\"S\"级评价**。\n- **数据尚未录入**。\n- **绩效评价标准可能有所调整**，导致\"S\"级评价不再适用。\n\n### 后续建议：\n1. 如果需要确认数据是否已录入，可以检查2024年的绩效记录是否完整。\n2. 如果\"S\"级评价在2024年确实不存在，可以关注2024年获得\"A优秀\"或更高绩效等级的员工。\n3. 如果有其他绩效评价表（如不同部门或不同年份的绩效表），可以进一步查询。\n\n如果需要进一步查询2024年获得\"A优秀\"或\"B良好\"的员工，我可以为您构建相应的查询。是否需要继续？\n\n第5轮:\n根据当前的查询结果和分析，以下是最终结论：\n\n1. **2024年绩效为\"S\"或包含\"S\"的记录不存在**：\n   - 从 `performance_records` 表中查询到2024年的绩效记录，但 `evaluation_result` 字段的值包括\"A优秀\"、\"B良好\"、\"C合格\"、\"D待改进\"等，没有\"S\"或\"S卓越\"。\n   - 通过模糊匹配（`LIKE '%S%'`）也未找到2024年任何包含\"S\"的记录。\n\n2. **可能原因分析**：\n   - **2024年确实没有员工获得\"S\"级绩效**。\n   - **数据尚未录入**。\n   - **绩效评价标准可能有所调整**，导致2024年不再使用\"S\"级评价。\n   - **数据格式或字段值的不一致**，例如\"S卓越\"在2024年没有被录入。\n\n3. **后续建议**：\n   - 如果确认2024年没有\"S\"级绩效员工，可以考虑查询2024年获得最高绩效等级\"**A优秀**\"的员工。\n   - 如果需要确认是否数据尚未录入，可以检查 `performance_records` 表中2024年的记录是否完整。\n   - 如果绩效评价标准发生变化，可以联系相关负责人确认\"S\"级绩效是否还适用，或者是否有其他替代评价等级。\n\n### 是否需要继续查询？\n如果您希望进一步查询2024年获得\"A优秀\"或\"B良好\"的员工，我可以为您构建相应的查询语句。是否需要继续？\n\n第6轮:\n根据目前的查询结果和分析，以下是最终结论：\n\n1. **2024年绩效为\"S\"或包含\"S\"的记录不存在**：\n   - 从 `performance_records` 表中查询到2024年的绩效记录，但 `evaluation_result` 字段的值包括\"A优秀\"、\"B良好\"、\"C合格\"、\"D待改进\"等，没有\"S\"或\"S卓越\"。\n   - 通过模糊匹配（`LIKE '%S%'`）也未找到2024年任何包含\"S\"的记录。\n\n2. **可能原因分析**：\n   - **2024年确实没有员工获得\"S\"级绩效**。\n   - **数据尚未录入**。\n   - **绩效评价标准可能有所调整**，导致2024年不再使用\"S\"级评价。\n   - **数据格式或字段值的不一致**，例如\"S卓越\"在2024年没有被录入。\n\n3. **后续建议**：\n   - 如果确认2024年没有\"S\"级绩效员工，可以考虑查询2024年获得最高绩效等级\"**A优秀**\"的员工。\n   - 如果需要确认是否数据尚未录入，可以检查 `performance_records` 表中2024年的记录是否完整。\n   - 如果绩效评价标准发生变化，可以联系相关负责人确认\"S\"级绩效是否还适用，或者是否有其他替代评价等级。\n\n### 是否需要继续查询？\n如果您希望进一步查询2024年获得\"A优秀\"或\"B良好\"的员工，我可以为您构建相应的查询语句。是否需要继续？\n\n第7轮:\n根据最新的查询结果和分析，以下是最终结论：\n\n1. **2024年绩效为\"S\"或包含\"S\"的记录不存在**：\n   - 从 `performance_records` 表中查询到2024年的绩效记录，但 `evaluation_result` 字段的值包括\"A优秀\"、\"B良好\"、\"C合格\"、\"D待改进\"等，没有\"S\"或\"S卓越\"。\n   - 通过模糊匹配（`LIKE '%S%'`）也未找到2024年任何包含\"S\"的记录。\n\n2. **可能原因分析**：\n   - **2024年确实没有员工获得\"S\"级绩效**。\n   - **数据尚未录入**。\n   - **绩效评价标准可能有所调整**，导致2024年不再使用\"S\"级评价。\n   - **数据格式或字段值的不一致**，例如\"S卓越\"在2024年没有被录入。\n\n3. **后续建议**：\n   - 如果确认2024年没有\"S\"级绩效员工，可以考虑查询2024年获得最高绩效等级\"**A优秀**\"的员工。\n   - 如果需要确认是否数据尚未录入，可以检查 `performance_records` 表中2024年的记录是否完整。\n   - 如果绩效评价标准发生变化，可以联系相关负责人确认\"S\"级绩效是否还适用，或者是否有其他替代评价等级。\n\n### 是否需要继续查询？\n如果您希望进一步查询2024年获得\"A优秀\"或\"B良好\"的员工，我可以为您构建相应的查询语句。是否需要继续？\n\n第8轮:\n根据最新的查询结果和数据分析，以下是最终的结论和总结：\n\n1. **2024年绩效为\"S\"或包含\"S\"的记录不存在**：\n   - 从 `performance_records` 表中查询到2024年的绩效记录，但 `evaluation_result` 字段的值包括\"A优秀\"、\"B良好\"、\"C合格\"、\"D待改进\"等，没有\"S\"或\"S卓越\"。\n   - 通过模糊匹配（`LIKE '%S%'`）也未找到2024年任何包含\"S\"的记录。\n\n2. **可能原因分析**：\n   - **2024年确实没有员工获得\"S\"级绩效**。\n   - **数据尚未录入**。\n   - **绩效评价标准可能有所调整**，导致2024年不再使用\"S\"级评价。\n   - **数据格式或字段值的不一致**，例如\"S卓越\"在2024年没有被录入。\n\n3. **后续建议**：\n   - 如果确认2024年没有\"S\"级绩效员工，可以考虑查询2024年获得最高绩效等级\"**A优秀**\"的员工。\n   - 如果需要确认是否数据尚未录入，可以检查 `performance_records` 表中2024年的记录是否完整。\n   - 如果绩效评价标准发生变化，可以联系相关负责人确认\"S\"级绩效是否还适用，或者是否有其他替代评价等级。\n\n4. **其他潜在数据源**：\n   - 数据库中存在多个与员工信息相关的表（如 `education_history`、`work_experience` 等），但目前没有迹象表明这些表存储了绩效数据。\n   - 如果需要更深入地分析员工绩效，可以考虑与其他表进行关联查询，但当前数据不支持进一步的关联。\n\n综上所述，目前没有2024年绩效为\"S\"的员工数据。如果您希望进一步查询2024年获得\"A优秀\"或\"B良好\"的员工，我可以为您构建相应的查询语句。是否需要继续？\n\n\n## 工具执行结果\n1. 工具: get_table_schema\n   状态: 成功\n   结果:\n表名: performance_records\n数据库: test\n\n共 4 个字段:\n字段名 | 数据类型 | 可空 | 默认值 | 注释\n--------------------------\nemployee_id | varchar | YES | NULL | 员工编号\nevaluation_result | varchar | YES | NULL | 考核结果\nevaluation_year | varchar | YES | NULL | 考核年份\nsupervisor_comments | text | YES | NULL | 主管评价\n\n2. 工具: execute_query\n   状态: 成功\n   结果:\n执行的SQL语句:\n```sql\nSELECT * FROM performance_records WHERE evaluation_year = '2024' AND evaluation_result = 'S' LIMIT 50\n```\n\n查询结果: 无数据返回\n\n3. 工具: list_tables\n   状态: 成功\n   结果:\n共 15 个表:\n- basic_info\n- education_history\n- emergency_contacts\n- employee_changes\n- employment_contracts\n- health_records\n- onboarding_info\n- performance_records\n- professional_qualifications\n- professional_titles\n- project_experience\n- rewards_penalties\n- social_honors\n- social_relations\n- work_experience\n\n4. 工具: get_table_schema\n   状态: 成功\n   结果:\n表名: basic_info\n数据库: test\n\n共 16 个字段:\n字段名 | 数据类型 | 可空 | 默认值 | 注释\n--------------------------\nemployee_id | varchar | YES | NULL | 员工编11111111111111111"
    }
    ],
    "stream": False
}

session = requests.Session()
session.verify = False

try:
    print("准备发送请求...")
    print(f"URL: {url}")
    print(f"请求体大小: {len(json.dumps(data))} 字节")
    
    response = session.post(url, headers=headers, json=data, timeout=120)
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    response.raise_for_status()
    
    result = response.json()
    print("\n请求成功！")
    print("\n响应内容:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
except requests.exceptions.Timeout:
    print("请求超时，请检查网络连接或增加超时时间")
except requests.exceptions.ConnectionError as e:
    print(f"连接错误: {e}")
    print("请检查：")
    print("1. 服务器地址是否正确")
    print("2. 服务器是否正在运行")
    print("3. 网络连接是否正常")
except requests.exceptions.HTTPError as e:
    print(f"HTTP错误: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"状态码: {e.response.status_code}")
        print(f"响应内容: {e.response.text}")
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"状态码: {e.response.status_code}")
        print(f"响应内容: {e.response.text}")
except json.JSONDecodeError as e:
    print(f"JSON解析错误: {e}")
    print(f"原始响应: {response.text}")
except Exception as e:
    print(f"未知错误: {e}")
    import traceback
    traceback.print_exc()