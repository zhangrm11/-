# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

# --- 数据加载逻辑 ---
# 使用Streamlit的缓存机制，避免每次用户交互都重新加载Excel文件，提高效率。
@st.cache_data
def load_thresholds_from_excel(file_path):
        """
        从指定的Excel文件加载BMI临界值数据。
        """
        try:
                df = pd.read_excel(file_path)
                required_columns = [
                        '年龄 (岁)', '男孩超重 (BMI)', '男孩肥胖 (BMI)',
                        '女孩超重 (BMI)', '女孩肥胖 (BMI)'
                ]
                if not all(col in df.columns for col in required_columns):
                        # st.error来显示错误信息
                        st.error(f"Excel文件缺少必需的列。请确保包含: {required_columns}")
                        return None

        except FileNotFoundError:
                st.error(f"错误：无法找到文件 '{file_path}'。")
                st.warning("请确保名为 'table_weight.xlsx' 的Excel文件与本应用脚本在同一目录下。")
                return None
        except Exception as e:
                st.error(f"读取Excel文件时发生错误: {e}")
                return None

        thresholds = {}
        for index, row in df.iterrows():
                age_key = f"{row['年龄 (岁)']:.1f}"
                thresholds[age_key] = {
                        "男": {"超重": row['男孩超重 (BMI)'], "肥胖": row['男孩肥胖 (BMI)']},
                        "女": {"超重": row['女孩超重 (BMI)'], "肥胖": row['女孩肥胖 (BMI)']}
                }
        return thresholds


# --- 核心计算逻辑 ---
def check_weight_status(age: float, height_m: float, weight_kg: float, gender: str, thresholds: dict):
        """
        根据输入的个人信息和BMI标准，判断体重状况。
        """
        # 年龄范围检查
        if not (2.0 <= age <= 18.0):
                return f"年龄 {age} 超出范围 (2.0-18.0岁)，无法评估。", None, None, None

        # 计算BMI
        bmi = weight_kg / (height_m ** 2)

        # 查找对应的BMI临界值
        age_key = f"{age:.1f}"
        if age_key not in thresholds:
                return f"数据源中未找到年龄为 {age_key} 的精确数据，请检查Excel文件。", None, None, None

        limits = thresholds[age_key][gender]
        overweight_limit = limits["超重"]
        obese_limit = limits["肥胖"]

        # 比较并确定状况
        if bmi < overweight_limit:
                result_status = "正常"
        elif overweight_limit <= bmi < obese_limit:
                result_status = "超重"
        else:
                result_status = "肥胖"

        return result_status, bmi, overweight_limit, obese_limit


# --- 主程序入口 & 网站界面 ---
def main():
        # --- 网站基础信息配置 ---
        st.set_page_config(page_title="儿童青少年体重评估", page_icon="🍎")

        # --- 加载数据 ---
        EXCEL_FILE_NAME = "table_weight.xlsx"
        BMI_THRESHOLDS = load_thresholds_from_excel(EXCEL_FILE_NAME)

        # --- 网站主体内容 ---
        st.title("儿童青少年体重状况评估工具")
        st.markdown("本工具适用于 **2岁至18岁** 的儿童及青少年")

        if BMI_THRESHOLDS is None:
                st.stop()

        # --- 创建表单来接收用户输入 ---
        with st.form("bmi_form"):
                st.subheader("请输入您的信息")

                # 创建左右两列来布局输入框
                col1, col2 = st.columns(2)
                with col1:
                        input_age = st.number_input("年龄 (岁)", min_value=2.0, max_value=18.0, step=0.1, format="%.1f",
                                                    help="请输入2.0到18.0之间的年龄")
                        input_height = st.number_input("身高 (米)", min_value=0.5, max_value=2.5, step=0.01,
                                                       format="%.2f", help="例如: 1.30")

                with col2:
                        input_gender = st.radio("性别", ("男", "女"))
                        input_weight = st.number_input("体重 (公斤)", min_value=10.0, max_value=200.0, step=0.1,
                                                       format="%.1f", help="例如: 30.5")

                # 表单提交按钮
                submitted = st.form_submit_button("开始评估")

        # --- 当用户点击按钮后，执行评估并显示结果 ---
        if submitted:
                # 验证输入
                if not (input_height > 0 and input_weight > 0):
                        st.error("身高和体重必须是大于零的有效数值")
                else:
                        # 调用函数进行评估
                        status, bmi, overweight, obese = check_weight_status(input_age, input_height, input_weight,
                                                                             input_gender, BMI_THRESHOLDS)

                        # 根据返回结果显示信息
                        if bmi is not None:
                                st.subheader("评估结果")

                                # 使用不同颜色展示结果
                                if status == "正常":
                                        st.success(f"您的体重状况为：【{status}】")
                                elif status == "超重":
                                        st.warning(f"您的体重状况为：【{status}】")
                                elif status == "肥胖":
                                        st.error(f"您的体重状况为：【{status}】")

                                # 显示详细信息
                                st.metric(label="您的BMI值", value=f"{bmi:.2f}")
                                st.write(
                                        f"年龄: {input_age}岁 | 性别: {input_gender} | 身高: {input_height}米 | 体重: {input_weight}公斤")
                                st.info(f"参考标准：\n- 超重临界值 (BMI): {overweight}\n- 肥胖临界值 (BMI): {obese}")

                        else:
                                # 如果 check_weight_status 返回了错误信息
                                st.error(status)


if __name__ == "__main__":
        main()