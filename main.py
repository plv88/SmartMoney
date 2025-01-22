import asyncio
from datetime import datetime, timezone
from app.core import SmartMoneyAnalyzer, DataBase, DataBaseTarget
import time


async def main(is_first_run: bool):
    if is_first_run:
        dict_signal = {'pair': 'BTCUSDT',
                       'ts_start': int(datetime.strptime('2024-12-31 03:00:00', '%Y-%m-%d %H:%M:%S')
                                       .replace(tzinfo=timezone.utc).timestamp()) * 1000,
                       'result': None}
        dict_result = await SmartMoneyAnalyzer(dict_signal).main()
        data_db = DataBase(dict_result)
    else:
        data_db = DataBase()
    bd_target = DataBaseTarget()
    while True:
        time_start = time.time()
        dict_signal = bd_target.get_one_new_trade()
        if dict_signal is None:
            break
        dict_result = await SmartMoneyAnalyzer(dict_signal).main()
        if isinstance(dict_result, dict):
            data_db.insert_data_from_dict(dict_result)
        else:
            bd_target.set_status('bad', dict_signal['id'])
        print(f'{datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]} Done {time.time() - time_start}')


# async def q_main(batch_size=4):
#     # if is_first_run:
#     #     def_pair = 'BTCUSDT'
#     #     def_timestamp = int(datetime.strptime('2024-12-31 03:00:00', '%Y-%m-%d %H:%M:%S')
#     #                         .replace(tzinfo=timezone.utc).timestamp()) * 1000
#     #     dict_result = await SmartMoneyAnalyzer(pair=def_pair, end_time=def_timestamp).main()
#     #     dict_result['target'] = None
#     #     data_db = DataBase(dict_result)
#     # else:
#     #     data_db = DataBase()
#     data_db = DataBase()
#     bd_target = DataBaseTarget()
#     while True:
#         time_start = time.time()
#         lst_dict_signal = [bd_target.get_one_new_trade() for _ in range(batch_size)]
#         if lst_dict_signal[0] is None:
#             break
#         lst_tasks = [SmartMoneyAnalyzer(dict_signal=dict_signal).main() for dict_signal in lst_dict_signal]
#         lst_dict_result = await asyncio.gather(*lst_tasks)
#         for dict_result, dict_signal in zip(lst_dict_result, lst_dict_signal):
#             if isinstance(dict_result, dict):
#                 data_db.insert_data_from_dict(dict_result)
#             else:
#                 bd_target.set_status('bad', dict_signal['id'])
#         print(f'{datetime.now(timezone.utc).strftime('%H:%M:%S.%f')[:-3]} Done {time.time() - time_start}')


if __name__ == "__main__":
    asyncio.run(main(is_first_run=True))
    # asyncio.run(q_main())
