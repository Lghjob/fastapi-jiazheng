from datetime import date

class DateUtils:
    """
    日期工具类
    """
    @staticmethod
    def get_last_month_first_day() -> date:
        """
        计算上个月的第一天
        :return: 上个月第一天的 date 对象
        """
        today = date.today()
        current_month = today.month
        current_year = today.year

        # 如果当前是1月，上个月为去年12月
        if current_month == 1:
            return date(current_year - 1, 12, 1)
        else:
            # 否则返回本年、上月、1号
            return date(current_year, current_month - 1, 1)