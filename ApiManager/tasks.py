# Create your tasks here
from __future__ import absolute_import, unicode_literals

import os
import shutil
import time

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist

from ApiManager.models import ProjectInfo
from ApiManager.utils.common import timestamp_to_datetime, getAllYml
from ApiManager.utils.emails import send_email_reports
from ApiManager.utils.operation import add_test_reports
from ApiManager.utils.runner import run_by_project, run_by_module, run_by_suite
from ApiManager.utils.testcase import get_time_stamp,dump_yaml_to_dict,fail_request_handle
from httprunner import HttpRunner
from loguru import logger


@shared_task
def main_hrun(testset_path, report_name):
    """
    用例运行
    :param testset_path: dict or list
    :param report_name: str
    :return:
    """
    logger.info("运行用例")

    runner = HttpRunner()
    test_dic,error_requests = [],[]
    getAllYml(testset_path, test_dic)
    for test_case_dir in test_dic:
        logger.info("当前运行的用例文件为：{}".format(test_case_dir))
        try:
            runner.run_path(test_case_dir)
        except Exception as e:
            fail_request_datas = dump_yaml_to_dict(test_case_dir)
            fail_data = fail_request_handle(fail_request_datas, str(e))
            error_requests.append(fail_data)
            logger.info("%s 接口处理报错: %s" % (fail_request_datas['config']['name'], str(e)))

    shutil.rmtree(testset_path)
    summary = timestamp_to_datetime(runner.get_summary(), type=False)
    if error_requests:
        for err_request in error_requests:
            for err in err_request:
                summary['step_datas'].append(err)
    case_id = summary.pop('case_id')
    if not case_id:
        summary['case_id'] = str(int(time.time()))
    report_path = add_test_reports(summary, report_name=report_name)
    os.remove(report_path)


@shared_task
def project_hrun(name, base_url, project, receiver):
    """
    异步运行整个项目
    :param env_name: str: 环境地址
    :param project: str
    :return:
    """
    logger.info("异步运行整个项目")
    runner = HttpRunner()
    id = ProjectInfo.objects.get(project_name=project).id

    testcase_dir_path = os.path.join(os.getcwd(), "suite")
    testcase_dir_path = os.path.join(testcase_dir_path, get_time_stamp())

    run_by_project(id, base_url, testcase_dir_path)

    test_dic,error_requests = [],[]
    getAllYml(testcase_dir_path, test_dic)
    for test_case_dir in test_dic:
        logger.info("当前运行的用例文件为：{}".format(test_case_dir))
        try:
            runner.run_path(test_case_dir)
        except Exception as e:
            fail_request_datas = dump_yaml_to_dict(test_case_dir)
            fail_data = fail_request_handle(fail_request_datas, str(e))
            error_requests.append(fail_data)
            logger.info("%s 接口处理报错: %s" % (fail_request_datas['config']['name'], str(e)))
    shutil.rmtree(testcase_dir_path)
    summary = timestamp_to_datetime(runner.get_summary(), type=False)
    if error_requests:
        for err_request in error_requests:
            for err in err_request:
                summary['step_datas'].append(err)
    case_id = summary.pop('case_id')
    if not case_id:
        summary['case_id'] = str(int(time.time()))
    report_path = add_test_reports(summary, report_name=name)

    if receiver != '':
        send_email_reports(receiver, report_path)
    os.remove(report_path)


@shared_task
def module_hrun(name, base_url, module, receiver):
    """
    异步运行模块
    :param env_name: str: 环境地址
    :param project: str：项目所属模块
    :param module: str：模块名称
    :return:
    """
    logger.info("异步运行模块")
    runner = HttpRunner()
    module = list(module)

    testcase_dir_path = os.path.join(os.getcwd(), "suite")
    testcase_dir_path = os.path.join(testcase_dir_path, get_time_stamp())

    try:
        for value in module:
            run_by_module(value[0], base_url, testcase_dir_path)
    except ObjectDoesNotExist:
        return '找不到模块信息'

    test_dic, error_requests = [], []
    getAllYml(testcase_dir_path, test_dic)
    for test_case_dir in test_dic:
        logger.info("当前运行的用例文件为：{}".format(test_case_dir))
        try:
            runner.run_path(test_case_dir)
        except Exception as e:
            fail_request_datas = dump_yaml_to_dict(test_case_dir)
            fail_data = fail_request_handle(fail_request_datas, str(e))
            error_requests.append(fail_data)
            logger.info("%s 接口处理报错: %s" % (fail_request_datas['config']['name'], str(e)))
    shutil.rmtree(testcase_dir_path)
    summary = timestamp_to_datetime(runner.get_summary(), type=False)
    if error_requests:
        for err_request in error_requests:
            for err in err_request:
                summary['step_datas'].append(err)
    case_id = summary.pop('case_id')
    if not case_id:
        summary['case_id'] = str(int(time.time()))


    report_path = add_test_reports(runner, report_name=name)

    if receiver != '':
        send_email_reports(receiver, report_path)
    os.remove(report_path)


@shared_task
def suite_hrun(name, base_url, suite, receiver):
    """
    异步运行模块
    :param env_name: str: 环境地址
    :param project: str：项目所属模块
    :param module: str：模块名称
    :return:
    """
    logger.info("异步运行模块")

    runner = HttpRunner()
    suite = list(suite)

    testcase_dir_path = os.path.join(os.getcwd(), "suite")
    testcase_dir_path = os.path.join(testcase_dir_path, get_time_stamp())

    try:
        for value in suite:
            run_by_suite(value[0], base_url, testcase_dir_path)
    except ObjectDoesNotExist:
        return '找不到Suite信息'

    test_dic, error_requests = [], []
    getAllYml(testcase_dir_path, test_dic)
    for test_case_dir in test_dic:
        logger.info("当前运行的用例文件为：{}".format(test_case_dir))
        try:
            runner.run_path(test_case_dir)
        except Exception as e:
            fail_request_datas = dump_yaml_to_dict(test_case_dir)
            fail_data = fail_request_handle(fail_request_datas, str(e))
            error_requests.append(fail_data)
            logger.info("%s 接口处理报错: %s" % (fail_request_datas['config']['name'], str(e)))
    shutil.rmtree(testcase_dir_path)
    summary = timestamp_to_datetime(runner.get_summary(), type=False)
    if error_requests:
        for err_request in error_requests:
            for err in err_request:
                summary['step_datas'].append(err)
    case_id = summary.pop('case_id')
    if not case_id:
        summary['case_id'] = str(int(time.time()))
    report_path = add_test_reports(runner, report_name=name)

    if receiver != '':
        send_email_reports(receiver, report_path)
    os.remove(report_path)
