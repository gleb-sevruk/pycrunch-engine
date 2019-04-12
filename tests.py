def run():

    from pprint import pprint

    from diagnostics import print_coverage

    cover = True
    import io

    if cover:
        import coverage
        exclude_list = [
            '*PyCharm.app/Contents/helpers/pydev/pydevd_file_utils.py',
            '*PyCharm.app/Contents/helpers/pydev/_pydevd_bundle/pydevd_comm.py'
        ]
        cov = coverage.Coverage(config_file=False, branch=True, omit=exclude_list)
        cov.start()



    import playground
    playground.my_sum()


    if cover:
        cov.stop()
        # creates .coverage file on disk
        # cov.save()
        # cov.report()

        output_file = io.StringIO()
        percentage = cov.report(file=output_file)
        # this modifies my filer as : playground.py.cover
        # anon = cov.annotate()
        file_getvalue = output_file.getvalue()
        print(file_getvalue)

        input_file = io.StringIO(output_file.getvalue())
        # coverage_data = cov.get_data()
        # print_coverage(coverage_data, cov)
        return cov
        # cov.html_report()

if __name__ == '__main__':
    run()