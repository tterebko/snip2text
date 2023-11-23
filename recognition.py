from cnocr import CnOcr


engine = CnOcr(rec_model_name='densenet_lite_136-gru', det_model_name='db_resnet34', rec_model_backend='pytorch', det_model_backend='pytorch')